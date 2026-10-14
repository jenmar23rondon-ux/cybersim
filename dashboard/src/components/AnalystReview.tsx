import type { AnalystReview as Review } from "../types";

export function AnalystReview({ review }: { review: Review }) {
  return (
    <section className="analyst-review" aria-label="Qué miraría un analista">
      <h3>Qué miraría un analista</h3>
      <ol>
        <li><strong>Fuente del log:</strong> {review.log_source}</li>
        <li><strong>Event ID / campo real:</strong> {review.event_reference}</li>
        <li><strong>Decisión:</strong> <span className={review.decision === "escalar" ? "analyst-escalate" : ""}>
          {review.decision || "Pendiente"}</span>. {review.note}</li>
      </ol>
    </section>
  );
}
