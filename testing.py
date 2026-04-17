# testing.py
#
# Tests unitarios de la capa de dominio de NexaPOS.
#
# ALCANCE:
#   Cubre excepciones, schemas (DTOs), modelos de entidad y specifications.
#   Estos tests NO necesitan Supabase ni ningún servicio externo —
#   prueban solo la lógica pura del dominio.
#
# EJECUCIÓN:
#   python testing.py
#
# CONVENCIÓN:
#   Cada grupo de tests imprime su sección.
#   Al final se reporta: N pasaron, M fallaron.
#   Exit code 0 = todo verde, 1 = hay fallos.

import sys
import os
import io
# Forzar UTF-8 en Windows para los caracteres del reporte
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_tests():
    passed = 0
    failed = 0
    errors = []

    def test(name: str, fn):
        nonlocal passed, failed
        try:
            fn()
            print(f"  ✓  {name}")
            passed += 1
        except AssertionError as e:
            print(f"  ✗  {name}")
            print(f"       AssertionError: {e}")
            failed += 1
            errors.append((name, str(e)))
        except Exception as e:
            print(f"  ✗  {name}")
            print(f"       {type(e).__name__}: {e}")
            failed += 1
            errors.append((name, f"{type(e).__name__}: {e}"))

    # ══════════════════════════════════════════════════════════════
    # 1. EXCEPCIONES DE DOMINIO
    # ══════════════════════════════════════════════════════════════
    print("\n▶  domain/exceptions")

    from domain.exceptions import (
        NexaPOSError, ValidationError, AuthenticationError, AuthorizationError,
        BusinessRuleError, InsufficientPaymentError, InsufficientStockError,
        DuplicateBarcodeError, EmptyCartError, NotFoundError, RepositoryError,
    )

    def test_hierarchy():
        assert issubclass(ValidationError,        NexaPOSError)
        assert issubclass(AuthenticationError,    NexaPOSError)
        assert issubclass(AuthorizationError,     NexaPOSError)
        assert issubclass(BusinessRuleError,      NexaPOSError)
        assert issubclass(InsufficientPaymentError, BusinessRuleError)
        assert issubclass(InsufficientStockError,   BusinessRuleError)
        assert issubclass(DuplicateBarcodeError,    BusinessRuleError)
        assert issubclass(EmptyCartError,           BusinessRuleError)
        assert issubclass(RepositoryError,        NexaPOSError)
    test("jerarquía de clases es correcta", test_hierarchy)

    def test_validation_error_field():
        ex = ValidationError("email", "El email es requerido")
        assert ex.field == "email"
        assert "email" in str(ex).lower()
    test("ValidationError expone .field con el nombre del campo", test_validation_error_field)

    def test_insufficient_payment_attrs():
        ex = InsufficientPaymentError(100.0, 80.0)
        assert ex.total    == 100.0
        assert ex.received == 80.0
        assert "100.00" in str(ex)
        assert "80.00"  in str(ex)
    test("InsufficientPaymentError guarda total y received", test_insufficient_payment_attrs)

    def test_insufficient_stock_attrs():
        ex = InsufficientStockError("Coca-Cola", 2, 5)
        assert ex.product_name == "Coca-Cola"
        assert ex.available    == 2
        assert ex.requested    == 5
        assert "Coca-Cola" in str(ex)
    test("InsufficientStockError guarda producto, disponible y solicitado", test_insufficient_stock_attrs)

    def test_not_found_includes_id():
        ex = NotFoundError("Product", "abc-123")
        assert "Product"  in str(ex)
        assert "abc-123"  in str(ex)
    test("NotFoundError incluye entidad e identificador en el mensaje", test_not_found_includes_id)

    def test_not_found_no_id():
        ex = NotFoundError("Tenant")
        assert "Tenant" in str(ex)
        assert ex.identifier == ""
    test("NotFoundError funciona sin identificador", test_not_found_no_id)

    def test_empty_cart_error():
        ex = EmptyCartError()
        assert isinstance(ex, BusinessRuleError)
        assert "vacío" in str(ex).lower()
    test("EmptyCartError es BusinessRuleError con mensaje de carrito vacío", test_empty_cart_error)

    # ══════════════════════════════════════════════════════════════
    # 2. SCHEMAS / DTOs
    # ══════════════════════════════════════════════════════════════
    print("\n▶  domain/schemas — Auth")

    from domain.schemas.auth_schemas import LoginRequest, RegisterRequest

    def test_login_valid():
        req = LoginRequest(email="test@example.com", password="secret123")
        req.validate()  # no debe lanzar
    test("LoginRequest válido no lanza excepción", test_login_valid)

    def test_login_empty_email():
        req = LoginRequest(email="", password="secret")
        try:
            req.validate()
            assert False, "Debería lanzar"
        except ValidationError as ex:
            assert ex.field == "email"
    test("LoginRequest email vacío → ValidationError(email)", test_login_empty_email)

    def test_login_invalid_email_format():
        req = LoginRequest(email="notanemail", password="secret")
        try:
            req.validate()
            assert False
        except ValidationError as ex:
            assert ex.field == "email"
    test("LoginRequest sin @ → ValidationError(email)", test_login_invalid_email_format)

    def test_login_empty_password():
        req = LoginRequest(email="a@b.com", password="")
        try:
            req.validate()
            assert False
        except ValidationError as ex:
            assert ex.field == "password"
    test("LoginRequest contraseña vacía → ValidationError(password)", test_login_empty_password)

    def test_register_short_password():
        req = RegisterRequest(email="a@b.com", password="123")
        try:
            req.validate()
            assert False
        except ValidationError as ex:
            assert ex.field == "password"
    test("RegisterRequest contraseña < 6 chars → ValidationError(password)", test_register_short_password)

    def test_register_valid():
        req = RegisterRequest(email="user@domain.com", password="secure99")
        req.validate()
    test("RegisterRequest válido no lanza excepción", test_register_valid)

    print("\n▶  domain/schemas — Products")

    from domain.schemas.product_schemas import CreateProductRequest, UpdateProductRequest

    def test_create_product_valid():
        req = CreateProductRequest(name="Refresco", price=15.0, cost=10.0)
        req.validate()
        d = req.to_db_dict("tenant-1")
        assert d["name"]      == "Refresco"
        assert d["price"]     == 15.0
        assert d["tenant_id"] == "tenant-1"
        assert d["barcode"]   is None
    test("CreateProductRequest válido genera db_dict correcto", test_create_product_valid)

    def test_create_product_empty_name():
        req = CreateProductRequest(name="   ", price=10.0)
        try:
            req.validate()
            assert False
        except ValidationError as ex:
            assert ex.field == "name"
    test("CreateProductRequest nombre en blanco → ValidationError(name)", test_create_product_empty_name)

    def test_create_product_zero_price():
        req = CreateProductRequest(name="X", price=0.0)
        try:
            req.validate()
            assert False
        except ValidationError as ex:
            assert ex.field == "price"
    test("CreateProductRequest precio=0 → ValidationError(price)", test_create_product_zero_price)

    def test_create_product_negative_price():
        req = CreateProductRequest(name="X", price=-1.0)
        try:
            req.validate()
            assert False
        except ValidationError as ex:
            assert ex.field == "price"
    test("CreateProductRequest precio negativo → ValidationError(price)", test_create_product_negative_price)

    def test_create_product_negative_cost():
        req = CreateProductRequest(name="X", price=10.0, cost=-5.0)
        try:
            req.validate()
            assert False
        except ValidationError as ex:
            assert ex.field == "cost"
    test("CreateProductRequest costo negativo → ValidationError(cost)", test_create_product_negative_cost)

    def test_create_product_barcode_stripped():
        req = CreateProductRequest(name="X", price=10.0, barcode="  123456  ")
        d = req.to_db_dict("t1")
        assert d["barcode"] == "123456"
    test("CreateProductRequest barcode limpia espacios en to_db_dict", test_create_product_barcode_stripped)

    def test_create_product_barcode_empty_is_none():
        req = CreateProductRequest(name="X", price=10.0, barcode="   ")
        d = req.to_db_dict("t1")
        assert d["barcode"] is None
    test("CreateProductRequest barcode solo espacios → None en db_dict", test_create_product_barcode_empty_is_none)

    def test_update_product_empty_returns_empty_dict():
        req = UpdateProductRequest()
        req.validate()
        assert req.to_db_dict() == {}
    test("UpdateProductRequest sin campos → to_db_dict vacío", test_update_product_empty_returns_empty_dict)

    def test_update_product_partial():
        req = UpdateProductRequest(name="Nuevo nombre", price=20.0)
        req.validate()
        d = req.to_db_dict()
        assert d == {"name": "Nuevo nombre", "price": 20.0}
    test("UpdateProductRequest parcial incluye solo los campos set", test_update_product_partial)

    print("\n▶  domain/schemas — Sales")

    from domain.schemas.sale_schemas import SaleItemRequest, CreateSaleRequest

    def test_sale_item_subtotal():
        item = SaleItemRequest("p1", "Coca-Cola", 3, 15.0)
        assert item.subtotal == 45.0
    test("SaleItemRequest.subtotal = cantidad × precio", test_sale_item_subtotal)

    def test_sale_item_zero_quantity():
        item = SaleItemRequest("p1", "Producto", 0, 15.0)
        try:
            item.validate()
            assert False
        except ValidationError as ex:
            assert ex.field == "quantity"
    test("SaleItemRequest cantidad=0 → ValidationError(quantity)", test_sale_item_zero_quantity)

    def test_sale_item_negative_price():
        item = SaleItemRequest("p1", "Producto", 1, -5.0)
        try:
            item.validate()
            assert False
        except ValidationError as ex:
            assert ex.field == "unit_price"
    test("SaleItemRequest precio negativo → ValidationError(unit_price)", test_sale_item_negative_price)

    def test_create_sale_total():
        items = [
            SaleItemRequest("p1", "A", 2, 10.0),
            SaleItemRequest("p2", "B", 1, 30.0),
        ]
        req = CreateSaleRequest(items=items, payment_method="cash", amount_received=60.0)
        assert req.total == 50.0
    test("CreateSaleRequest.total es la suma de subtotales", test_create_sale_total)

    def test_create_sale_empty_cart():
        req = CreateSaleRequest(items=[], payment_method="cash")
        try:
            req.validate()
            assert False
        except EmptyCartError:
            pass
    test("CreateSaleRequest carrito vacío → EmptyCartError", test_create_sale_empty_cart)

    def test_create_sale_invalid_payment_method():
        items = [SaleItemRequest("p1", "A", 1, 10.0)]
        req = CreateSaleRequest(items=items, payment_method="bitcoin")
        try:
            req.validate()
            assert False
        except ValidationError as ex:
            assert ex.field == "payment_method"
    test("CreateSaleRequest método inválido → ValidationError(payment_method)", test_create_sale_invalid_payment_method)

    def test_create_sale_insufficient_cash():
        items = [SaleItemRequest("p1", "A", 1, 100.0)]
        req = CreateSaleRequest(items=items, payment_method="cash", amount_received=50.0)
        try:
            req.validate()
            assert False
        except InsufficientPaymentError as ex:
            assert ex.total    == 100.0
            assert ex.received == 50.0
    test("CreateSaleRequest efectivo insuficiente → InsufficientPaymentError", test_create_sale_insufficient_cash)

    def test_create_sale_card_no_amount_required():
        items = [SaleItemRequest("p1", "A", 1, 100.0)]
        req = CreateSaleRequest(items=items, payment_method="card", amount_received=0)
        req.validate()  # card no valida monto recibido
    test("CreateSaleRequest con tarjeta no exige monto recibido", test_create_sale_card_no_amount_required)

    def test_create_sale_from_cart():
        cart = [
            {"id": "p1", "name": "Coca-Cola", "quantity": 2, "price": 15.0},
            {"id": "p2", "name": "Agua",      "quantity": 1, "price": 10.0},
        ]
        req = CreateSaleRequest.from_cart(cart, "card", 0)
        assert len(req.items)      == 2
        assert req.total           == 40.0
        assert req.payment_method  == "card"
        assert req.items[0].product_id == "p1"
    test("CreateSaleRequest.from_cart convierte lista de dicts correctamente", test_create_sale_from_cart)

    # ══════════════════════════════════════════════════════════════
    # 3. MODELOS DE DOMINIO
    # ══════════════════════════════════════════════════════════════
    print("\n▶  domain/models — Product")

    from domain.models.product import Product

    def test_product_margin():
        p = Product(id="1", name="X", price=100.0, tenant_id="t", cost=60.0)
        assert p.margin_pct  == 40.0
        assert p.profit      == 40.0
        assert p.is_profitable()
    test("Product.margin_pct y profit calculan correctamente", test_product_margin)

    def test_product_not_profitable():
        p = Product(id="1", name="X", price=5.0, tenant_id="t", cost=10.0)
        assert not p.is_profitable()
        assert p.profit < 0
    test("Product.is_profitable() retorna False cuando costo > precio", test_product_not_profitable)

    def test_product_zero_price_margin():
        p = Product(id="1", name="X", price=0.0, tenant_id="t")
        assert p.margin_pct == 0.0
    test("Product con precio=0 → margin_pct=0 (sin división por cero)", test_product_zero_price_margin)

    def test_product_from_dict():
        d = {
            "id": "abc", "name": "Refresco", "price": 15.0,
            "tenant_id": "t1", "cost": 10.0, "barcode": "12345",
            "category_id": None, "is_active": True,
        }
        p = Product.from_dict(d)
        assert p.id      == "abc"
        assert p.name    == "Refresco"
        assert p.barcode == "12345"
    test("Product.from_dict construye entidad desde dict de Supabase", test_product_from_dict)

    def test_product_roundtrip():
        d = {
            "id": "x", "name": "Test", "price": 10.0, "tenant_id": "t",
            "cost": 5.0, "barcode": None, "category_id": None, "is_active": True,
        }
        p  = Product.from_dict(d)
        d2 = p.to_dict()
        assert d2["name"]  == "Test"
        assert d2["price"] == 10.0
    test("Product from_dict → to_dict hace roundtrip correcto", test_product_roundtrip)

    print("\n▶  domain/models — Sale")

    from domain.models.sale import Sale, SaleItem

    def test_sale_item_subtotal():
        item = SaleItem("p1", "Coca", 3, 15.0)
        assert item.subtotal == 45.0
    test("SaleItem.subtotal = cantidad × precio unitario", test_sale_item_subtotal)

    def test_sale_items_count():
        sale = Sale(
            id="s1", tenant_id="t1", user_id="u1",
            total=50.0, status="completed", payment_method="cash",
            items=[SaleItem("p1", "A", 2, 10.0), SaleItem("p2", "B", 3, 10.0)],
        )
        assert sale.items_count == 5
        assert sale.is_completed
    test("Sale.items_count suma cantidades y is_completed funciona", test_sale_items_count)

    def test_sale_not_completed():
        sale = Sale(id="s1", tenant_id="t", user_id="u",
                    total=0, status="pending", payment_method="cash")
        assert not sale.is_completed
    test("Sale con status='pending' → is_completed False", test_sale_not_completed)

    # ══════════════════════════════════════════════════════════════
    # 4. SPECIFICATIONS
    # ══════════════════════════════════════════════════════════════
    print("\n▶  domain/specifications")

    from domain.specifications.low_stock_spec import (
        LowStockSpec, OutOfStockSpec, HealthyStockSpec,
    )

    def test_low_stock_below_minimum():
        spec = LowStockSpec()
        assert spec.is_satisfied_by({"stock_actual": 3, "stock_minimo": 5}) is True
    test("LowStockSpec: stock < mínimo → True", test_low_stock_below_minimum)

    def test_low_stock_at_minimum():
        spec = LowStockSpec()
        assert spec.is_satisfied_by({"stock_actual": 5, "stock_minimo": 5}) is True
    test("LowStockSpec: stock == mínimo → True (en el límite)", test_low_stock_at_minimum)

    def test_low_stock_above_minimum():
        spec = LowStockSpec()
        assert spec.is_satisfied_by({"stock_actual": 10, "stock_minimo": 5}) is False
    test("LowStockSpec: stock > mínimo → False", test_low_stock_above_minimum)

    def test_out_of_stock():
        spec = OutOfStockSpec()
        assert spec.is_satisfied_by({"stock_actual": 0})  is True
        assert spec.is_satisfied_by({"stock_actual": 1})  is False
    test("OutOfStockSpec: True solo cuando stock=0", test_out_of_stock)

    def test_healthy_stock():
        spec = HealthyStockSpec()
        assert spec.is_satisfied_by({"stock_actual": 20, "stock_minimo": 5}) is True
        assert spec.is_satisfied_by({"stock_actual": 5,  "stock_minimo": 5}) is False
    test("HealthyStockSpec: True cuando stock > mínimo*2", test_healthy_stock)

    def test_specification_filter():
        spec = LowStockSpec()
        inventory = [
            {"name": "A", "stock_actual": 2,  "stock_minimo": 5},
            {"name": "B", "stock_actual": 10, "stock_minimo": 5},
            {"name": "C", "stock_actual": 5,  "stock_minimo": 5},
        ]
        result = spec.filter(inventory)
        assert len(result) == 2
        assert result[0]["name"] == "A"
        assert result[1]["name"] == "C"
    test("Specification.filter() devuelve solo los que satisfacen la spec", test_specification_filter)

    def test_specification_count():
        spec   = LowStockSpec()
        items  = [
            {"stock_actual": 1, "stock_minimo": 5},
            {"stock_actual": 8, "stock_minimo": 5},
            {"stock_actual": 3, "stock_minimo": 5},
        ]
        assert spec.count(items) == 2
    test("Specification.count() cuenta candidatos que satisfacen", test_specification_count)

    def test_specification_and():
        low = LowStockSpec()
        out = OutOfStockSpec()
        both = low.and_(out)
        assert both.is_satisfied_by({"stock_actual": 0, "stock_minimo": 5}) is True
        assert both.is_satisfied_by({"stock_actual": 3, "stock_minimo": 5}) is False
    test("Specification.and_() combina dos specs con lógica AND", test_specification_and)

    def test_specification_or():
        low = LowStockSpec(threshold_factor=1.0)
        out = OutOfStockSpec()
        either = low.or_(out)
        assert either.is_satisfied_by({"stock_actual": 0, "stock_minimo": 5}) is True
        assert either.is_satisfied_by({"stock_actual": 3, "stock_minimo": 5}) is True
        assert either.is_satisfied_by({"stock_actual": 10, "stock_minimo": 5}) is False
    test("Specification.or_() combina dos specs con lógica OR", test_specification_or)

    def test_specification_not():
        healthy   = HealthyStockSpec()
        unhealthy = healthy.not_()
        assert unhealthy.is_satisfied_by({"stock_actual": 5,  "stock_minimo": 5}) is True
        assert unhealthy.is_satisfied_by({"stock_actual": 20, "stock_minimo": 5}) is False
    test("Specification.not_() invierte el resultado de la spec", test_specification_not)

    def test_low_stock_early_warning():
        # Con factor=2.0 alerta temprana: stock_actual <= stock_minimo*2
        spec = LowStockSpec(threshold_factor=2.0)
        assert spec.is_satisfied_by({"stock_actual": 8,  "stock_minimo": 5}) is True
        assert spec.is_satisfied_by({"stock_actual": 11, "stock_minimo": 5}) is False
    test("LowStockSpec con factor=2.0 da alerta temprana", test_low_stock_early_warning)

    # ══════════════════════════════════════════════════════════════
    # RESUMEN
    # ══════════════════════════════════════════════════════════════
    total = passed + failed
    print(f"\n{'═' * 55}")
    print(f"  Resultados: {passed}/{total} pasaron", end="")
    if failed:
        print(f", {failed} fallaron  ✗")
        print("\n  Fallos detallados:")
        for name, msg in errors:
            print(f"    • {name}")
            print(f"      {msg}")
    else:
        print("  ✓  Todo verde")
    print(f"{'═' * 55}")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
