export type TaxBand = {
  limite_superior: number | null;
  aliquota: number;
  deducao: number;
};

export type TaxTable = {
  ano_calendario?: number;
  exercicio?: number;
  versao_regras: string;
  vigencia_inicio: string;
  vigencia_fim: string | null;
  periodicidade: string;
  fonte: string;
  faixas: TaxBand[];
  deducao_dependente: number;
  desconto_simplificado_maximo: number;
  limite_educacao_por_beneficiario?: number;
};

export type TaxTablesResponse = {
  mensais: Record<string, TaxTable>;
  anuais: Record<string, TaxTable>;
};

export type MonthlyCalculationRequest = {
  ano: number;
  mes: number;
  renda_bruta: string;
  inss_contribuicao: string;
  dependentes: number;
  outras_deducoes: string;
  modalidade: "deducoes_legais" | "desconto_simplificado" | "mais_vantajosa";
};

export type AnnualCalculationRequest = {
  ano_calendario: number;
  rendimentos_tributaveis: string;
  rendimentos_isentos: string;
  irrf_retido: string;
  dependentes: number;
  despesas_medicas: string;
  despesas_educacionais: string[];
  previdencia_privada: string;
  outras_deducoes: string;
  modalidade: "deducoes_legais" | "desconto_simplificado" | "mais_vantajosa";
};

export type CalculationResponse = {
  tipo: "mensal" | "anual";
  resultado: Record<string, unknown>;
  comparacao?: Record<string, unknown>;
  memoria_calculo: Record<string, unknown>;
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...options,
      headers: { "Content-Type": "application/json", ...options?.headers },
    });
  } catch {
    throw new Error("Não foi possível conectar à API. Confirme se o backend está iniciado.");
  }

  const payload = await response.json().catch(() => ({})) as { detail?: unknown };
  if (!response.ok) {
    const detail = payload.detail;
    const message = typeof detail === "string"
      ? detail
      : Array.isArray(detail)
        ? detail.map((item) => typeof item === "object" && item !== null && "msg" in item ? String(item.msg) : String(item)).join(" ")
        : "Não foi possível concluir o cálculo.";
    throw new Error(message);
  }
  return payload as T;
}

export function fetchTaxTables() {
  return request<TaxTablesResponse>("/api/tabelas");
}

export function calculateMonthly(input: MonthlyCalculationRequest) {
  return request<CalculationResponse>("/api/calculos/mensal", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function calculateAnnual(input: AnnualCalculationRequest) {
  return request<CalculationResponse>("/api/calculos/anual", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function fetchCalculationMemory(
  type: "mensal" | "anual",
  input: MonthlyCalculationRequest | AnnualCalculationRequest,
) {
  return request<Record<string, unknown>>(`/api/memoria-calculo/${type}`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}
