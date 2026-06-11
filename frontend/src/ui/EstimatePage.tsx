import { useParams } from "react-router-dom";
import { EstimateView } from "./EstimateView";

export function EstimatePage() {
  const { estimateId } = useParams();
  return <EstimateView estimateId={estimateId ?? ""} readOnly={false} />;
}
