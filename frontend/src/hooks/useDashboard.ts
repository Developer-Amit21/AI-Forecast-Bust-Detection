import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { Explanation, Prediction, Variable } from '../types/api'

export function useDashboard(variable: Variable, leadDay: number) {
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [selected, setSelected] = useState<Prediction | null>(null)
  const [explanation, setExplanation] = useState<Explanation | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  useEffect(() => { let active = true; setLoading(true); api.latest(variable).then(rows => {
    if (!active) return; setPredictions(rows); const current = rows.find(row => row.lead_day === leadDay) ?? rows[0]; setSelected(current ?? null); setError(null)
  }).catch(e => active && setError(e.message)).finally(() => active && setLoading(false)); return () => { active = false } }, [variable, leadDay])
  useEffect(() => { if (!selected) return; api.explanation(selected.region_id, variable, leadDay).then(setExplanation).catch(e => setError(e.message)) }, [selected?.region_id, variable, leadDay])
  return { predictions, selected, setSelected, explanation, error, loading }
}
