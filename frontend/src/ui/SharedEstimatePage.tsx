import { useParams } from "react-router-dom";
import { EstimateView } from "./EstimateView";

export function SharedEstimatePage() {
  const { shareToken } = useParams();
  return <EstimateView shareToken={shareToken ?? ""} readOnly />;
}
