"""Products page implementation."""

from nicegui import APIRouter

from ...products.models import ProductRepository, Product
from ..components import frame
from ..components.model_detail_page import display_model_detail_page, create_model_view_action
from ..components.model_list_page import display_model_list_page


router = APIRouter(prefix="/products")


@router.page("/")
def products_page() -> None:
    """Render the products page with a table of all products."""
    repository = ProductRepository()

    # Create view action
    row_actions = {
        "view": create_model_view_action(
            repository=repository,
            dialog=False,
            detail_url="/products/{id}",
        )
    }

    # Render page
    with frame("Producten"):
        display_model_list_page(
            repository=repository,
            model_cls=Product,
            table_state_key="products_table",
            title="Producten",
            row_actions=row_actions,
            card_width="max-w-5xl",
            filter_placeholder="Zoek producten...",
        )


@router.page("/{product_id:int}")
def product_detail(product_id: int) -> None:
    """Render the product detail page."""
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
