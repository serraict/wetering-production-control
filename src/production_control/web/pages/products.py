"""Products page implementation."""

from nicegui import APIRouter

from ...products.models import ProductRepository, Product
from ..components import frame
from ..components.model_detail_page import display_model_detail_page, create_model_view_action
from ..components.model_list_page import display_model_list_page


router = APIRouter(prefix="/products")


@router.page("/")
def products_page() -> None:
    repository = ProductRepository()
    title = "Producten"

    row_actions = {
        "view": create_model_view_action(
            repository=repository,
            detail_url="/products/{id}",
        )
    }

    with frame(title):
        display_model_list_page(
            repository=repository,
            model_cls=Product,
            table_state_key="products_table",
            title=title,
            row_actions=row_actions,
        )


@router.page("/{product_id:int}")
def product_detail(product_id: int) -> None:
    repository = ProductRepository()
    product = repository.get_by_id(product_id)

    with frame("Product Details"):
        display_model_detail_page(
            model=product,
            title="Product Details",
            back_link_text="← Terug naar Producten",
            back_link_url="/products",
            model_title_field="name",
        )
