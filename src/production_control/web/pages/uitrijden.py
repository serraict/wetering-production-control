"""Uitrijden page implementation."""

from nicegui import APIRouter

from ...vloerplan.repositories import Vloerplan19cmRepository
from ...vloerplan.models import Vloerplan19cm
from ..components import frame
from ..components.model_detail_page import display_model_detail_page, create_model_view_action
from ..components.model_list_page import display_model_list_page


router = APIRouter(prefix="/uitrijden")


def get_repository() -> Vloerplan19cmRepository:
    return Vloerplan19cmRepository()


@router.page("/")
def uitrijden_page() -> None:
    row_actions = {
        "view": create_model_view_action(
            repository=get_repository(),
            dialog=True,
        ),
    }

    with frame("Uitrijden"):
        display_model_list_page(
            repository=get_repository(),
            model_cls=Vloerplan19cm,
            table_state_key="uitrijden_table",
            title="Uitrijden",
            row_actions=row_actions,
        )


@router.page("/{id}")
def uitrijden_detail(id: int) -> None:
    record = get_repository().get_by_id(id)

    with frame("Uitrijden Details"):
        display_model_detail_page(
            model=record,
            title="Uitrijden Details",
            back_link_text="← Terug naar Uitrijden",
            back_link_url="/uitrijden",
        )
