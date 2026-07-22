# Modeling Assumptions

1. **Trend model**: We use a log‑linear trend for Access and Usage (slowing growth near saturation). Linear is fallback.
2. **Event impacts**: We assume impacts are additive, have a fixed lag, and last indefinitely (permanent shift).
3. **Data gaps**: Missing years are interpolated for model fitting; this introduces uncertainty.
4. **External validity**: Impact magnitudes from other countries (Kenya) are applied to Ethiopia with adjustment.
5. **No seasonality**: No repeating seasonal patterns are modeled (data is annual/irregular).
6. **Scenarios**: Optimistic = impact × 1.3, Base = × 1.0, Pessimistic = × 0.6.
7. **Prediction intervals**: 95% PI from the trend model, combined with event impacts.
