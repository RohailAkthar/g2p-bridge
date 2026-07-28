import logging
from sqlalchemy import select, or_
from sqlalchemy.orm import sessionmaker

from ..engine import get_engine
from ..interface.mapper_interface import MapperInterface
from ..models import ResPartner
from ..schemas import ResolveRequest, ResolveResponse, ResolveResult

_logger = logging.getLogger("registry_db_mapper")
_engine = get_engine()
session_maker = sessionmaker(bind=_engine.get("db_engine_registry"), expire_on_commit=False)


class RegistryMapper(MapperInterface):
    async def resolve(self, resolve_request: ResolveRequest) -> ResolveResponse | None:
        """
        Resolves financial address directly from Odoo registry DB.
        """
        _logger.info(f"Resolving {len(resolve_request.beneficiary_ids)} IDs via Odoo DB query")
        results = []

        with session_maker() as session:
            for b_id in resolve_request.beneficiary_ids:
                try:
                    partner = None
                    # 1. Attempt lookup by partner database ID (if integer)
                    if b_id.isdigit():
                        partner = session.execute(
                            select(ResPartner).where(ResPartner.id == int(b_id))
                        ).scalars().first()

                    # 2. Lookup by pensioner_id (custom column on res_partner)
                    if not partner:
                        partner = session.execute(
                            select(ResPartner).where(ResPartner.pensioner_id == b_id)
                        ).scalars().first()

                    if not partner:
                        _logger.warning(f"Beneficiary {b_id} not found in Odoo Registry DB")
                        results.append(ResolveResult(id=b_id, status="NOT_FOUND"))
                        continue

                    # 3. Build Financial Address based on payment_mode
                    fa = None
                    if partner.payment_mode == "bank" and partner.account_num:
                        fa = {
                            "account_number": partner.account_num,
                            "bank_code": partner.bank_name,
                            "fa_type": "BANK_ACCOUNT"
                        }
                    elif partner.payment_mode == "mobile_wallet" and partner.mobile_wallet:
                        fa = {
                            "mobile_number": partner.mobile_wallet,
                            "fa_type": "MOBILE_WALLET"
                        }

                    # Construct nominee name without fallback
                    nominee_parts = [
                        partner.nominee_first_name,
                        partner.nominee_middle_name,
                        partner.nominee_last_name
                    ]
                    nominee_full_name = " ".join([str(p).strip() for p in nominee_parts if p and str(p).strip()])
                    resolved_name = nominee_full_name if nominee_full_name else None

                    if fa:
                        results.append(ResolveResult(
                            id=b_id,
                            fa=fa,
                            name=resolved_name,
                            status="SUCCESS"
                        ))
                    else:
                        _logger.warning(f"No valid financial details linked for beneficiary {b_id}")
                        results.append(ResolveResult(id=b_id, status="NO_FINANCIAL_DETAILS"))

                except Exception as ex:
                    _logger.error(f"Error resolving beneficiary {b_id}: {ex}")
                    results.append(ResolveResult(id=b_id, status="ERROR"))

        return ResolveResponse(results=results)
