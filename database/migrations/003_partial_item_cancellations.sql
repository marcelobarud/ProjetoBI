BEGIN;

ALTER TABLE sales.sales_order_items
    ADD COLUMN fulfilled_quantity BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN cancelled_quantity BIGINT NOT NULL DEFAULT 0,
    ADD CONSTRAINT ck_sales_order_items_resolution_nonnegative
        CHECK (fulfilled_quantity >= 0 AND cancelled_quantity >= 0),
    ADD CONSTRAINT ck_sales_order_items_resolution_cap
        CHECK (fulfilled_quantity + cancelled_quantity <= quantity);

CREATE TABLE sales.sales_order_item_cancellations (
    sales_order_item_cancellation_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    sales_order_id BIGINT NOT NULL,
    sales_order_item_id BIGINT NOT NULL,
    cancelled_quantity BIGINT NOT NULL,
    cancellation_reason VARCHAR(30) NOT NULL,
    cancelled_at TIMESTAMPTZ NOT NULL,
    gross_cancelled_amount NUMERIC(19,2) NOT NULL,
    discount_cancelled_amount NUMERIC(19,2) NOT NULL,
    net_cancelled_amount NUMERIC(19,2) NOT NULL,
    shipping_cancelled_amount NUMERIC(19,2) NOT NULL DEFAULT 0,
    external_reference VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_sales_order_item_cancellations PRIMARY KEY (sales_order_item_cancellation_id),
    CONSTRAINT uq_sales_order_item_cancellations_order_id
        UNIQUE (sales_order_id, sales_order_item_cancellation_id),
    CONSTRAINT fk_sales_order_item_cancellations_item
        FOREIGN KEY (sales_order_id, sales_order_item_id)
        REFERENCES sales.sales_order_items (sales_order_id, sales_order_item_id),
    CONSTRAINT ck_sales_order_item_cancellations_quantity CHECK (cancelled_quantity > 0),
    CONSTRAINT ck_sales_order_item_cancellations_reason CHECK (cancellation_reason = 'stock_timeout'),
    CONSTRAINT ck_sales_order_item_cancellations_amounts CHECK (
        gross_cancelled_amount >= 0 AND discount_cancelled_amount >= 0
        AND net_cancelled_amount >= 0 AND shipping_cancelled_amount >= 0
    ),
    CONSTRAINT ck_sales_order_item_cancellations_net CHECK (
        net_cancelled_amount = gross_cancelled_amount - discount_cancelled_amount
    )
);

CREATE INDEX idx_sales_order_item_cancellations_item
    ON sales.sales_order_item_cancellations (sales_order_id, sales_order_item_id, cancelled_at);
CREATE INDEX idx_sales_order_item_cancellations_order
    ON sales.sales_order_item_cancellations (sales_order_id, cancelled_at);

ALTER TABLE payments.refunds
    ADD COLUMN sales_order_item_cancellation_id BIGINT;
ALTER TABLE payments.refunds
    ADD CONSTRAINT fk_refunds_item_cancellation
        FOREIGN KEY (sales_order_id, sales_order_item_cancellation_id)
        REFERENCES sales.sales_order_item_cancellations (sales_order_id, sales_order_item_cancellation_id),
    ADD CONSTRAINT ck_refunds_single_origin CHECK (
        return_id IS NULL OR sales_order_item_cancellation_id IS NULL
    );
ALTER TABLE payments.refunds DROP CONSTRAINT ck_refunds_reason;
ALTER TABLE payments.refunds ADD CONSTRAINT ck_refunds_reason CHECK (
    reason_code IS NULL OR reason_code IN ('customer_request', 'return', 'duplicate_charge', 'other', 'stock_timeout')
);
CREATE INDEX idx_refunds_item_cancellation
    ON payments.refunds (sales_order_id, sales_order_item_cancellation_id)
    WHERE sales_order_item_cancellation_id IS NOT NULL;

CREATE FUNCTION sales.apply_item_fulfilled_quantity_delta(
    p_sales_order_id BIGINT, p_sales_order_item_id BIGINT, p_delta BIGINT
) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    UPDATE sales.sales_order_items
       SET fulfilled_quantity = fulfilled_quantity + p_delta
     WHERE sales_order_id = p_sales_order_id AND sales_order_item_id = p_sales_order_item_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Item de pedido ausente ao atualizar saldo expedido.' USING ERRCODE = '23503';
    END IF;
END;
$$;

CREATE FUNCTION sales.sync_fulfillment_item_quantity() RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        PERFORM sales.apply_item_fulfilled_quantity_delta(NEW.sales_order_id, NEW.sales_order_item_id, NEW.fulfilled_quantity);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        PERFORM sales.apply_item_fulfilled_quantity_delta(OLD.sales_order_id, OLD.sales_order_item_id, -OLD.fulfilled_quantity);
        RETURN OLD;
    ELSIF (OLD.sales_order_id, OLD.sales_order_item_id) IS DISTINCT FROM (NEW.sales_order_id, NEW.sales_order_item_id) THEN
        PERFORM sales.apply_item_fulfilled_quantity_delta(OLD.sales_order_id, OLD.sales_order_item_id, -OLD.fulfilled_quantity);
        PERFORM sales.apply_item_fulfilled_quantity_delta(NEW.sales_order_id, NEW.sales_order_item_id, NEW.fulfilled_quantity);
        RETURN NEW;
    ELSE
        PERFORM sales.apply_item_fulfilled_quantity_delta(NEW.sales_order_id, NEW.sales_order_item_id,
            NEW.fulfilled_quantity - OLD.fulfilled_quantity);
        RETURN NEW;
    END IF;
END;
$$;
CREATE TRIGGER trg_fulfillment_items_sync_item_quantity
AFTER INSERT OR UPDATE OR DELETE ON logistics.fulfillment_items
FOR EACH ROW EXECUTE FUNCTION sales.sync_fulfillment_item_quantity();

CREATE FUNCTION sales.sync_item_cancellation_quantity() RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE sales.sales_order_items
           SET cancelled_quantity = cancelled_quantity + NEW.cancelled_quantity
         WHERE sales_order_id = NEW.sales_order_id AND sales_order_item_id = NEW.sales_order_item_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE sales.sales_order_items
           SET cancelled_quantity = cancelled_quantity - OLD.cancelled_quantity
         WHERE sales_order_id = OLD.sales_order_id AND sales_order_item_id = OLD.sales_order_item_id;
        RETURN OLD;
    ELSIF (OLD.sales_order_id, OLD.sales_order_item_id) IS DISTINCT FROM (NEW.sales_order_id, NEW.sales_order_item_id) THEN
        UPDATE sales.sales_order_items SET cancelled_quantity = cancelled_quantity - OLD.cancelled_quantity
         WHERE sales_order_id = OLD.sales_order_id AND sales_order_item_id = OLD.sales_order_item_id;
        UPDATE sales.sales_order_items SET cancelled_quantity = cancelled_quantity + NEW.cancelled_quantity
         WHERE sales_order_id = NEW.sales_order_id AND sales_order_item_id = NEW.sales_order_item_id;
        RETURN NEW;
    ELSE
        UPDATE sales.sales_order_items
           SET cancelled_quantity = cancelled_quantity + NEW.cancelled_quantity - OLD.cancelled_quantity
         WHERE sales_order_id = NEW.sales_order_id AND sales_order_item_id = NEW.sales_order_item_id;
        RETURN NEW;
    END IF;
END;
$$;
CREATE TRIGGER trg_item_cancellations_sync_item_quantity
AFTER INSERT OR UPDATE OR DELETE ON sales.sales_order_item_cancellations
FOR EACH ROW EXECUTE FUNCTION sales.sync_item_cancellation_quantity();

COMMIT;
