import logging
from typing import List, Optional

import httpx
from openg2p_g2p_bridge_models.models import (
    FundsAvailableWithBankEnum,
    FundsBlockedWithBankEnum,
)
from pydantic import BaseModel

from ..bank_interface.bank_connector_interface import (
    BankConnectorInterface,
    BlockFundsResponse,
    CheckFundsResponse,
    DisbursementPaymentPayload,
    PaymentResponse,
    PaymentStatus,
)
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class BankPaymentPayload(BaseModel):
    payment_reference_number: str
    remitting_account: str
    remitting_account_currency: str
    payment_amount: float
    funds_blocked_reference_number: str
    beneficiary_name: str

    beneficiary_account: str
    beneficiary_account_currency: str
    beneficiary_account_type: str
    beneficiary_bank_code: str
    beneficiary_branch_code: Optional[str] = None

    beneficiary_mobile_wallet_provider: Optional[str] = None
    beneficiary_phone_no: Optional[str] = None

    beneficiary_email: Optional[str] = None
    beneficiary_email_wallet_provider: Optional[str] = None

    narrative_1: Optional[str] = None
    narrative_2: Optional[str] = None
    narrative_3: Optional[str] = None
    narrative_4: Optional[str] = None
    narrative_5: Optional[str] = None
    narrative_6: Optional[str] = None

    payment_date: str


class ExampleBankConnector(BankConnectorInterface):
    def check_funds(self, account_number, currency, amount) -> CheckFundsResponse:
        _logger.info(
            f"Checking funds availability for account_number: {account_number}, currency: {currency}, amount: {amount}"
        )
        try:
            with httpx.Client() as client:
                request_data = {
                    "account_number": account_number,
                    "account_currency": currency,
                    "total_funds_needed": amount,
                }
                response = client.post(_config.funds_available_check_url_example_bank, json=request_data)
                response.raise_for_status()

                data = response.json()
                if data["status"] == "success":
                    _logger.info(
                        f"Funds available for account_number: {account_number}, currency: {currency}, amount: {amount}"
                    )
                    return CheckFundsResponse(
                        status=FundsAvailableWithBankEnum.FUNDS_AVAILABLE, error_code=""
                    )
                _logger.info(
                    f"Funds not available for account_number: {account_number}, currency: {currency}, amount: {amount}"
                )
                return CheckFundsResponse(
                    status=FundsAvailableWithBankEnum.FUNDS_NOT_AVAILABLE, error_code=""
                )
        except httpx.HTTPStatusError as e:
            _logger.error(
                f"Error checking funds availability for account_number: {account_number}, currency: {currency}, amount: {amount}"
            )
            return CheckFundsResponse(status=FundsAvailableWithBankEnum.PENDING_CHECK, error_code=str(e))

    def block_funds(self, account_number, currency, amount) -> BlockFundsResponse:
        _logger.info(
            f"Blocking funds for account_number: {account_number}, currency: {currency}, amount: {amount}"
        )
        try:
            with httpx.Client() as client:
                request_data = {
                    "account_number": account_number,
                    "currency": currency,
                    "amount": amount,
                }
                response = client.post(_config.funds_block_url_example_bank, json=request_data)
                response.raise_for_status()

                data = response.json()
                if data["status"] == "success":
                    _logger.info(
                        f"Funds blocked for account_number: {account_number}, currency: {currency}, amount: {amount}"
                    )
                    return BlockFundsResponse(
                        status=FundsBlockedWithBankEnum.FUNDS_BLOCK_SUCCESS,
                        block_reference_no=data["block_reference_no"],
                        error_code="",
                    )
                _logger.error(
                    f"Funds block failed for account_number: {account_number}, currency: {currency}, amount: {amount}"
                )
                return BlockFundsResponse(
                    status=FundsBlockedWithBankEnum.FUNDS_BLOCK_FAILURE,
                    block_reference_no="",
                    error_code=data.get("error_code", ""),
                )
        except httpx.HTTPStatusError as e:
            _logger.error(
                f"Error blocking funds for account_number: {account_number}, currency: {currency}, amount: {amount}"
            )
            return BlockFundsResponse(
                status=FundsBlockedWithBankEnum.FUNDS_BLOCK_FAILURE,
                block_reference_no="",
                error_code=str(e),
            )

    def initiate_payment(
        self, disbursement_payment_payloads: List[DisbursementPaymentPayload]
    ) -> PaymentResponse:
        import os
        import httpx

        _logger.info(f"Initiating payment via API/Excel export for {len(disbursement_payment_payloads)} disbursements")
        try:
            api_url = os.getenv("G2P_BRIDGE_API_URL", "http://localhost:8000")
            if not api_url.endswith("/"):
                api_url += "/"
            endpoint = f"{api_url}write_dispatch_file"

            payloads_data = [payload.model_dump() for payload in disbursement_payment_payloads]

            try:
                _logger.info(f"Sending dispatch data to API server: {endpoint}")
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(endpoint, json=payloads_data)
                    response.raise_for_status()
                    _logger.info("Successfully sent dispatch data to API server.")
            except Exception as e:
                _logger.warning(f"Failed to send dispatch data to API server: {e}. Backup generation will handle this.")

            return PaymentResponse(status=PaymentStatus.SUCCESS, error_code="")
        except Exception as e:
            _logger.error(f"Error initiating payment: {e}")
            return PaymentResponse(status=PaymentStatus.ERROR, error_code=str(e))

    def retrieve_reconciliation_id(
        self, bank_reference: str, customer_reference: str, narratives: str
    ) -> str:
        _logger.info(
            f"Retrieving reconciliation id for bank_reference: {bank_reference}, customer_reference: {customer_reference}"
        )
        # The disbursement_id is carried in the MT940 :86: field (narrative_5 ->
        # narratives[4]) because the :61: customer-reference is limited to 16
        # chars and disbursement ids can be longer. Fall back to the :61:
        # customer reference for statements produced before this change (which
        # only ever carried short ids there).
        if narratives and len(narratives) > 4 and str(narratives[4]).strip():
            return str(narratives[4]).strip()
        return customer_reference

    def retrieve_beneficiary_name(self, narratives: str) -> str:
        _logger.info(f"Retrieving beneficiary name from narratives: {narratives}")
        return narratives[3]

    def retrieve_reversal_reason(self, narratives: str) -> str:
        _logger.info(f"Retrieving reversal reason from narratives: {narratives}")
        return narratives[-1]
