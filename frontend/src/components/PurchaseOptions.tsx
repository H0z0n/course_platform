import { useState } from "react";
import { Link, useLocation } from "react-router";
import { toApiError } from "../api/client";
import { api } from "../api/endpoints";
import type { CourseOutline } from "../api/types";
import { isStaff, useAuth } from "../auth/AuthContext";
import { formatPrice } from "../lib/format";
import { useSite } from "../site/SiteContext";
import { Modal } from "./ui";

interface Offer {
  kind: "course" | "module";
  id: number;
  title: string;
  price: string;
}

function collectOffers(course: CourseOutline, onlyModuleId?: number): Offer[] {
  const offers: Offer[] = [];
  if (course.price !== null) {
    offers.push({ kind: "course", id: course.id, title: course.title, price: course.price });
  }
  for (const module of course.modules) {
    if (module.price === null || module.is_purchased) continue;
    if (onlyModuleId !== undefined && module.id !== onlyModuleId) continue;
    offers.push({ kind: "module", id: module.id, title: module.title, price: module.price });
  }
  return offers;
}

function CheckoutDialog({
  offer,
  onClose,
  onDone,
}: {
  offer: Offer;
  onClose: () => void;
  onDone: () => void;
}) {
  const { currency } = useSite();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function pay() {
    setPending(true);
    setError(null);
    try {
      await api.purchases.checkout(
        offer.kind === "course" ? { course_id: offer.id } : { module_id: offer.id },
      );
      onDone();
    } catch (reason) {
      setError(toApiError(reason).message);
      setPending(false);
    }
  }

  return (
    <Modal title="Оформление покупки" onClose={onClose}>
      <p className="muted">{offer.kind === "course" ? "Весь курс" : "Модуль"}</p>
      <p className="checkout-title">{offer.title}</p>
      <p className="checkout-price">{formatPrice(offer.price, currency)}</p>
      <div className="alert alert-info">
        Это тестовая оплата: деньги не списываются, доступ откроется сразу.
      </div>
      {error && <div className="alert alert-error">{error}</div>}
      <div className="modal-actions">
        <button type="button" className="btn" onClick={onClose} disabled={pending}>
          Отмена
        </button>
        <button type="button" className="btn btn-primary" onClick={pay} disabled={pending}>
          {pending ? "Оплачиваем…" : "Оплатить"}
        </button>
      </div>
    </Modal>
  );
}

export function PurchaseOptions({
  course,
  onPurchased,
  onlyModuleId,
}: {
  course: CourseOutline;
  onPurchased: () => void;
  onlyModuleId?: number;
}) {
  const { user } = useAuth();
  const { currency, demo_payments } = useSite();
  const location = useLocation();
  const [selected, setSelected] = useState<Offer | null>(null);

  if (course.is_purchased) {
    return <div className="alert alert-success">Курс куплен — все уроки открыты.</div>;
  }
  if (isStaff(user)) {
    return <div className="alert alert-info">Вы администратор: все уроки открыты без покупки.</div>;
  }

  const offers = collectOffers(course, onlyModuleId);
  if (offers.length === 0) {
    return (
      <p className="muted">
        Платные уроки этого курса не продаются онлайн — доступ выдаёт администратор.
      </p>
    );
  }

  return (
    <div className="offers">
      {offers.map((offer) => (
        <div key={`${offer.kind}-${offer.id}`} className="offer">
          <div>
            <div className="offer-title">
              {offer.kind === "course" ? "Весь курс" : `Модуль «${offer.title}»`}
            </div>
            <div className="offer-price">{formatPrice(offer.price, currency)}</div>
          </div>
          {user ? (
            demo_payments && (
              <button type="button" className="btn btn-primary" onClick={() => setSelected(offer)}>
                Купить
              </button>
            )
          ) : (
            <Link to="/login" state={{ from: location.pathname }} className="btn btn-primary">
              Войти и купить
            </Link>
          )}
        </div>
      ))}
      {user && !demo_payments && (
        <p className="muted small">
          Онлайн-оплата пока не подключена. Чтобы получить доступ, свяжитесь с администратором.
        </p>
      )}
      {selected && (
        <CheckoutDialog
          offer={selected}
          onClose={() => setSelected(null)}
          onDone={() => {
            setSelected(null);
            onPurchased();
          }}
        />
      )}
    </div>
  );
}
