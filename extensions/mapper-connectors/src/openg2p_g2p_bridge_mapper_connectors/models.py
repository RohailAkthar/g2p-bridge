from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import mapped_column


class ResPartner(BaseORMModel):
    __tablename__ = "res_partner"

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String, nullable=True)
    active = mapped_column(Boolean, nullable=True)
    is_registrant = mapped_column(Boolean, nullable=True)
    pensioner_id = mapped_column(String, nullable=True, index=True)
    benf_zan_id = mapped_column(String, nullable=True, index=True)

    # Custom payment fields stored in Odoo's res_partner table
    payment_mode = mapped_column(String, nullable=True)
    bank_name = mapped_column(String, nullable=True)
    account_num = mapped_column(String, nullable=True)
    account_name = mapped_column(String, nullable=True)
    mobile_wallet = mapped_column(String, nullable=True)
