import { useEffect, useState } from "react";
import {
  Activity, ArrowDownRight, ArrowUpRight, BadgeCheck, BookOpen, CalendarDays,
  Calculator, Check, ChevronDown, ChevronRight, CircleHelp, Clock3, FileText,
  HeartPulse, History, Info, Landmark, Menu, RefreshCw, ShieldCheck, Sparkles,
  Wallet, X, LoaderCircle, type LucideIcon,
} from "lucide-react";
import {
  calculateAnnual, calculateMonthly, fetchCalculationMemory, fetchTaxTables,
  type AnnualCalculationRequest, type CalculationResponse, type MonthlyCalculationRequest,
  type TaxTable, type TaxTablesResponse,
} from "./api";

type Section = "calculator" | "deductions" | "rules" | "updates" | "history" | "about";
type Mode = "monthly" | "annual";
type FormField = "rendaBruta" | "inss" | "dependentes" | "outrasDeducoesMensais" | "rendimentosTributaveis" | "rendimentosIsentos" | "irrfRetido" | "despesasMedicas" | "despesasEducacionais" | "previdenciaPrivada" | "outrasDeducoesAnuais";
type FormValues = Record<FormField, string>;
type LastRequest =
  | { type: "mensal"; input: MonthlyCalculationRequest }
  | { type: "anual"; input: AnnualCalculationRequest };

const navItems: { id: Section; label: string; icon: LucideIcon }[] = [
  { id: "calculator", label: "Calculadora", icon: Calculator },
  { id: "deductions", label: "Deduções", icon: Wallet },
  { id: "rules", label: "Tabelas e regras", icon: BookOpen },
  { id: "updates", label: "Atualizações", icon: RefreshCw },
  { id: "history", label: "Histórico", icon: History },
  { id: "about", label: "Sobre o projeto", icon: CircleHelp },
];

const sectionCopy: Record<Exclude<Section, "calculator">, { title: string; subtitle: string; icon: LucideIcon }> = {
  deductions: { title: "Deduções", subtitle: "Compare as modalidades previstas para a sua declaração.", icon: Wallet },
  rules: { title: "Tabelas e regras", subtitle: "Consulte as faixas cadastradas e seus períodos de vigência.", icon: BookOpen },
  updates: { title: "Atualizações tributárias", subtitle: "Acompanhe as fontes e o processo de revisão das tabelas.", icon: RefreshCw },
  history: { title: "Histórico de simulações", subtitle: "Suas simulações aparecerão aqui quando o recurso for conectado.", icon: History },
  about: { title: "Sobre a calculadora", subtitle: "Estimativas claras, regras versionadas e revisão antes de publicar mudanças.", icon: CircleHelp },
};

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const percentages = new Intl.NumberFormat("pt-BR", { style: "percent", maximumFractionDigits: 1 });
const initialForm: FormValues = {
  rendaBruta: "", inss: "", dependentes: "0", outrasDeducoesMensais: "",
  rendimentosTributaveis: "", rendimentosIsentos: "", irrfRetido: "",
  despesasMedicas: "", despesasEducacionais: "", previdenciaPrivada: "",
  outrasDeducoesAnuais: "",
};

function App() {
  const [section, setSection] = useState<Section>("calculator");
  const [mode, setMode] = useState<Mode>("monthly");
  const [year, setYear] = useState(2026);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [legalDeductions, setLegalDeductions] = useState(true);
  const [tables, setTables] = useState<TaxTablesResponse | null>(null);
  const [tablesLoading, setTablesLoading] = useState(true);
  const [form, setForm] = useState<FormValues>(initialForm);
  const [calculation, setCalculation] = useState<CalculationResponse | null>(null);
  const [lastRequest, setLastRequest] = useState<LastRequest | null>(null);
  const [memory, setMemory] = useState<Record<string, unknown> | null>(null);
  const [memoryOpen, setMemoryOpen] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [loadingMemory, setLoadingMemory] = useState(false);
  const yearTables = Object.entries(tables?.mensais ?? {}).filter(([key]) => key.startsWith(String(year)));
  const monthlyDate = `${year}-${String(month).padStart(2, "0")}-01`;
  const monthlyTable = yearTables.map(([, table]) => table).find((candidate) => candidate.vigencia_inicio <= monthlyDate && (!candidate.vigencia_fim || monthlyDate <= candidate.vigencia_fim)) ?? null;
  const annualTable = tables?.anuais[String(year)] ?? null;
  const table = mode === "annual" ? annualTable : monthlyTable;

  useEffect(() => {
    let mounted = true;
    fetchTaxTables()
      .then((loadedTables) => { if (mounted) setTables(loadedTables); })
      .catch((error: unknown) => { if (mounted) setMessage(errorMessage(error)); })
      .finally(() => { if (mounted) setTablesLoading(false); });
    return () => { mounted = false; };
  }, []);

  function openSection(nextSection: Section) {
    setSection(nextSection);
    setSidebarOpen(false);
  }

  function clearCalculation() {
    setCalculation(null);
    setLastRequest(null);
    setMemory(null);
    setMemoryOpen(false);
  }

  function updateField(field: FormField, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
    clearCalculation();
  }

  async function runCalculation() {
    setCalculating(true);
    setMessage("");
    clearCalculation();
    try {
      const dependentes = parseDependents(form.dependentes);
      const modalidade = legalDeductions ? "deducoes_legais" : "desconto_simplificado";
      if (mode === "monthly") {
        const input: MonthlyCalculationRequest = {
          ano: year,
          mes: month,
          renda_bruta: normalizeMoney(form.rendaBruta, "Salário bruto", true),
          inss_contribuicao: normalizeMoney(form.inss, "Contribuição ao INSS"),
          dependentes,
          outras_deducoes: normalizeMoney(form.outrasDeducoesMensais, "Outras deduções legais"),
          modalidade,
        };
        const response = await calculateMonthly(input);
        setCalculation(response);
        setMemory(response.memoria_calculo);
        setLastRequest({ type: "mensal", input });
      } else {
        const education = normalizeMoney(form.despesasEducacionais, "Despesas educacionais");
        const input: AnnualCalculationRequest = {
          ano_calendario: year,
          rendimentos_tributaveis: normalizeMoney(form.rendimentosTributaveis, "Rendimentos tributáveis", true),
          rendimentos_isentos: normalizeMoney(form.rendimentosIsentos, "Rendimentos isentos"),
          irrf_retido: normalizeMoney(form.irrfRetido, "Imposto retido na fonte"),
          dependentes,
          despesas_medicas: normalizeMoney(form.despesasMedicas, "Despesas médicas"),
          despesas_educacionais: education === "0.00" ? [] : [education],
          previdencia_privada: normalizeMoney(form.previdenciaPrivada, "Previdência privada"),
          outras_deducoes: normalizeMoney(form.outrasDeducoesAnuais, "Outras deduções"),
          modalidade,
        };
        const response = await calculateAnnual(input);
        setCalculation(response);
        setMemory(response.memoria_calculo);
        setLastRequest({ type: "anual", input });
      }
    } catch (error) {
      setMessage(errorMessage(error));
    } finally {
      setCalculating(false);
    }
  }

  async function showCalculationMemory() {
    if (!lastRequest) return;
    if (memoryOpen) {
      setMemoryOpen(false);
      return;
    }
    setLoadingMemory(true);
    setMessage("");
    try {
      const loadedMemory = await fetchCalculationMemory(lastRequest.type, lastRequest.input);
      setMemory(loadedMemory);
      setMemoryOpen(true);
    } catch (error) {
      setMessage(errorMessage(error));
    } finally {
      setLoadingMemory(false);
    }
  }

  function changeMode(nextMode: Mode) {
    setMode(nextMode);
    clearCalculation();
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
        <div className="brand-lockup">
          <div className="brand-mark"><Landmark size={21} strokeWidth={2.1} /></div>
          <div><strong>IRPF Brasil</strong><span>Calculadora de renda</span></div>
          <button className="sidebar-close icon-button" onClick={() => setSidebarOpen(false)} aria-label="Fechar menu"><X size={18} /></button>
        </div>
        <div className="nav-caption">ESPAÇO DE TRABALHO</div>
        <nav className="side-nav" aria-label="Navegação principal">
          {navItems.map(({ id, label, icon: Icon }) => (
            <button key={id} className={`nav-item ${section === id ? "nav-item-active" : ""}`} onClick={() => openSection(id)}>
              <Icon size={17} strokeWidth={1.9} /><span>{label}</span>{section === id && <ChevronRight className="nav-chevron" size={15} />}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="status-card"><div className="status-icon"><BadgeCheck size={17} /></div><div><strong>Tabelas versionadas</strong><p>Regras locais com fontes para conferência.</p></div></div>
          <div className="sidebar-footnote"><ShieldCheck size={14} /> Seus dados não saem desta tela</div>
        </div>
      </aside>
      {sidebarOpen && <button className="sidebar-scrim" aria-label="Fechar menu" onClick={() => setSidebarOpen(false)} />}

      <div className="main-column">
        <header className="topbar">
          <button className="mobile-menu icon-button" onClick={() => setSidebarOpen(true)} aria-label="Abrir menu"><Menu size={20} /></button>
          <div className="topbar-context"><span>IRPF</span><ChevronRight size={13} /><strong>{section === "calculator" ? "Calculadora" : sectionCopy[section].title}</strong></div>
          <div className="topbar-tools">
            <label className="year-control"><CalendarDays size={16} /><span>Ano-calendário</span>
              <select value={year} onChange={(event) => { setYear(Number(event.target.value)); clearCalculation(); }} aria-label="Ano-calendário"><option value={2026}>2026</option><option value={2025}>2025</option></select><ChevronDown className="select-chevron" size={13} />
            </label>
            <div className="topbar-divider" />
            <div className="table-status"><span className="status-pulse" /><span><strong>{tablesLoading ? "Carregando tabela" : table ? "Tabela validada" : "Tabela indisponível"}</strong><small>{table ? `Vigência desde ${formatDate(table.vigencia_inicio)}` : "Selecione um período disponível"}</small></span></div>
          </div>
        </header>

        <main className="page-content">
          {section === "calculator" ? <CalculatorPage mode={mode} setMode={changeMode} year={year} month={month} setMonth={(nextMonth: number) => { setMonth(nextMonth); clearCalculation(); }} table={table} tablesLoading={tablesLoading} form={form} onFieldChange={updateField} legalDeductions={legalDeductions} setLegalDeductions={(enabled: boolean) => { setLegalDeductions(enabled); clearCalculation(); }} calculation={calculation} calculating={calculating} memory={memory} memoryOpen={memoryOpen} loadingMemory={loadingMemory} onCalculate={runCalculation} onShowMemory={showCalculationMemory} onShowRules={() => openSection("rules")} /> : <SecondaryPage section={section} year={year} tables={tables} onOpenCalculator={() => openSection("calculator")} />}
        </main>
        <footer className="app-footer"><span>Calculadora de Imposto de Renda</span><span>Projeto independente · estimativas sujeitas à validação</span></footer>
      </div>
      {message && <div className="toast" role="alert"><Info size={17} />{message}<button className="icon-button" onClick={() => setMessage("")} aria-label="Fechar aviso"><X size={16} /></button></div>}
    </div>
  );
}

function CalculatorPage({ mode, setMode, year, month, setMonth, table, tablesLoading, form, onFieldChange, legalDeductions, setLegalDeductions, calculation, calculating, memory, memoryOpen, loadingMemory, onCalculate, onShowMemory, onShowRules }: {
  mode: Mode; setMode: (mode: Mode) => void; year: number; month: number; setMonth: (month: number) => void;
  table: TaxTable | null; tablesLoading: boolean; form: FormValues; onFieldChange: (field: FormField, value: string) => void;
  legalDeductions: boolean; setLegalDeductions: (enabled: boolean) => void;
  calculation: CalculationResponse | null; calculating: boolean; memory: Record<string, unknown> | null;
  memoryOpen: boolean; loadingMemory: boolean; onCalculate: () => void; onShowMemory: () => void; onShowRules: () => void;
}) {
  const result = calculation?.resultado ?? null;
  const taxKey = mode === "monthly" ? "imposto" : "imposto_devido";
  const netLabel = mode === "monthly"
    ? "Renda após IR"
    : asNumber(result?.restituicao_estimada) > 0 ? "Restituição estimada" : "Imposto a pagar";
  const netValue = mode === "monthly"
    ? result?.renda_apos_ir
    : asNumber(result?.restituicao_estimada) > 0 ? result?.restituicao_estimada : result?.imposto_a_pagar;
  const scenarios = calculation?.comparacao?.cenarios as Record<string, Record<string, unknown>> | undefined;
  const appliedMode = calculation?.memoria_calculo.modalidade_aplicada;
  const selectedLabel = appliedMode === "desconto_simplificado" ? "Desconto simplificado" : "Deduções legais";
  const bestLabel = calculation?.comparacao?.mais_vantajosa === "desconto_simplificado" ? "Desconto simplificado" : "Deduções legais";
  return <>
    <div className="page-heading"><div><div className="eyebrow"><span className="eyebrow-dot" /> PLANEJAMENTO TRIBUTÁRIO</div><h1>Calculadora de Imposto de Renda</h1><p>Uma visão organizada para entender sua estimativa de IR.</p></div><div className="heading-tag"><ShieldCheck size={15} /> Ambiente privado</div></div>
    <div className="dashboard-grid">
      <section className="main-stack" aria-label="Dados da simulação">
        <div className="panel calculator-panel">
          <div className="panel-heading"><div className="panel-title-icon"><Calculator size={19} /></div><div><h2>Nova simulação</h2><p>Preencha os dados para preparar seu cálculo.</p></div></div>
          <div className="mode-switch" role="tablist" aria-label="Tipo de cálculo">
            <button className={mode === "monthly" ? "mode-active" : ""} role="tab" aria-selected={mode === "monthly"} onClick={() => setMode("monthly")}><Activity size={15} /> Mensal · IRRF</button>
            <button className={mode === "annual" ? "mode-active" : ""} role="tab" aria-selected={mode === "annual"} onClick={() => setMode("annual")}><FileText size={15} /> Anual · IRPF</button>
          </div>
          {mode === "monthly" ? <MonthlyForm values={form} onChange={onFieldChange} month={month} setMonth={setMonth} /> : <AnnualForm year={year} values={form} onChange={onFieldChange} />}
          <div className="deduction-choice">
            <div className="section-label"><span>Deduções</span><span className="optional-label">OPCIONAL</span><Info size={14} /></div>
            <label className={`choice-row ${legalDeductions ? "choice-selected" : ""}`}><input type="radio" name="deduction-mode" checked={legalDeductions} onChange={() => setLegalDeductions(true)} /><span className="choice-copy"><strong>Deduções legais</strong><small>Use as despesas permitidas pela legislação.</small></span>{legalDeductions && <span className="choice-check"><Check size={12} /></span>}</label>
            <label className={`choice-row ${!legalDeductions ? "choice-selected" : ""}`}><input type="radio" name="deduction-mode" checked={!legalDeductions} onChange={() => setLegalDeductions(false)} /><span className="choice-copy"><strong>Desconto simplificado</strong><small>Compare com o abatimento limitado previsto em lei.</small></span>{!legalDeductions && <span className="choice-check"><Check size={12} /></span>}</label>
            <button className="text-link" onClick={onCalculate}>Comparar modalidades <ChevronRight size={14} /></button>
          </div>
          <button className="primary-button calculate-button" onClick={onCalculate} disabled={calculating || tablesLoading}><Calculator size={16} /> {calculating ? "Calculando..." : "Calcular imposto"} {calculating ? <LoaderCircle className="loading-icon" size={15} /> : <ArrowUpRight size={15} />}</button>
          <p className="form-disclaimer"><ShieldCheck size={13} /> Os valores são enviados apenas ao backend local desta aplicação.</p>
        </div>

        <div className="result-panel">
          <div className="result-topline"><div className="result-heading"><span className="result-icon"><Check size={15} /></span><div><h2>Resultado da estimativa</h2><p>{mode === "monthly" ? `IRRF · ${String(month).padStart(2, "0")}/${year}` : `Exercício ${year + 1} · ano-calendário ${year}`}</p></div></div><span className="pending-pill">{result ? "Cálculo concluído" : calculating ? "Calculando" : "Aguardando dados"}</span></div>
          <div className="result-metrics"><Metric label="Base de cálculo" value={result ? currencyText(result.base_calculo) : "—"} /><Metric label="Alíquota efetiva" value={result ? percentageText(result.aliquota_efetiva) : "—"} /><Metric label={mode === "monthly" ? "IRRF estimado" : "Imposto devido"} value={result ? currencyText(result[taxKey]) : "—"} /></div>
          <div className="net-result"><div className="net-icon"><Wallet size={17} /></div><div><span>{netLabel}</span><strong>{result ? currencyText(netValue) : "—"}</strong></div><p>{result ? `Modalidade usada: ${selectedLabel}. Mais vantajosa: ${bestLabel} · diferença ${currencyText(calculation?.comparacao?.diferenca_entre_modalidades)}` : "Informe os valores para calcular usando a tabela oficial do período."}</p></div>
          {result && <button className="text-link memory-toggle" onClick={onShowMemory} disabled={loadingMemory}>{loadingMemory ? <LoaderCircle size={14} className="loading-icon" /> : <Info size={14} />}{memoryOpen ? "Ocultar memória de cálculo" : "Como esse imposto foi calculado?"}</button>}
          {memoryOpen && memory && <div className="memory-details"><MemoryRow label="Rendimentos considerados" value={memory.rendimentos_considerados} />{mode === "monthly" ? <><MemoryRow label="INSS informado" value={currencyText(memory.inss_informado)} /><MemoryRow label="Outras deduções informadas" value={currencyText(memory.outras_deducoes_informadas)} /></> : <MemoryRow label="IRRF retido" value={currencyText(memory.irrf_retido)} />}<MemoryRow label="Deduções utilizadas" value={memory.deducoes_utilizadas} /><MemoryRow label="Faixa e alíquota" value={memory.faixa_numero ? `Faixa ${memory.faixa_numero} · ${percentageText(memory.aliquota)}` : "Ver deduções acima"} /><MemoryRow label="Parcela a deduzir" value={currencyText(memory.parcela_deduzir)} /><MemoryRow label="Imposto antes da redução" value={currencyText(memory.imposto_tabela)} /><MemoryRow label="Redução legal" value={currencyText(memory.reducao)} /><MemoryRow label="Versão das regras" value={memory.versao_regras} /><p>{String(memory.formula_base ?? "")}</p><p>{String(memory.formula_imposto ?? "")}</p><a href={sourceUrl(String(memory.fonte ?? ""))} target="_blank" rel="noreferrer">Fonte oficial <ArrowUpRight size={12} /></a></div>}
          {scenarios && <div className="comparison-inline"><span>Legal: {currencyText(getScenarioTax(scenarios.deducoes_legais, mode))}</span><span>Simplificado: {currencyText(getScenarioTax(scenarios.desconto_simplificado, mode))}</span></div>}
        </div>
      </section>

      <aside className="side-stack" aria-label="Informações da tabela">
        <div className="panel summary-panel">
          <div className="side-panel-heading"><span className="side-icon navy"><FileText size={15} /></span><div><h2>Resumo da simulação</h2><p>Ano-calendário {year}</p></div><button className="icon-button" aria-label="Sobre o resumo"><Info size={15} /></button></div>
          <div className="summary-rows"><SummaryRow label="Rendimentos tributáveis" value={result ? currencyText(mode === "monthly" ? result.renda_bruta : result.rendimentos_tributaveis) : "—"} /><SummaryRow label="Rendimentos isentos" value={result && mode === "annual" ? currencyText(result.rendimentos_isentos) : "—"} /><SummaryRow label="Deduções informadas" value={result ? currencyText(result.deducoes) : "—"} /><div className="summary-divider" /><SummaryRow label="Base de cálculo" value={result ? currencyText(result.base_calculo) : "—"} strong /><SummaryRow label="Imposto estimado" value={result ? currencyText(result[taxKey]) : "—"} strong /></div>
          <div className="info-callout"><div className="callout-icon"><Sparkles size={15} /></div><div><strong>Sobre a estimativa</strong><p>O cálculo usa as regras versionadas para o período. Confira as deduções e fontes oficiais antes de tomar decisões.</p></div></div>
        </div>
        <div className="panel rates-panel">
          <div className="side-panel-heading"><span className="side-icon blue"><Landmark size={15} /></span><div><h2>Faixas de tributação</h2><p>{year} · {mode === "monthly" ? "mensal" : "anual"}</p></div><button className="icon-button" onClick={onShowRules} aria-label="Ver tabela completa"><ArrowUpRight size={15} /></button></div>
          <RateTable table={table} /><button className="text-link rates-link" onClick={onShowRules}>Ver tabela e vigência <ChevronRight size={14} /></button>
        </div>
        <div className="update-card"><div className="update-card-icon"><RefreshCw size={16} /></div><div><strong>Regras com histórico</strong><p>As tabelas atuais têm fonte e período registrados. Mudanças exigem revisão antes da publicação.</p><span className="update-state"><span /> Revisão humana</span></div></div>
        <div className="source-card"><div className="source-title"><ShieldCheck size={15} /><strong>Fontes cadastradas</strong></div><a href={sourceUrl(table?.fonte ?? "")} target="_blank" rel="noreferrer">Receita Federal <ArrowUpRight size={12} /></a><a href="https://www.planalto.gov.br" target="_blank" rel="noreferrer">Legislação Federal <ArrowUpRight size={12} /></a><small>Consulte a publicação oficial antes de usar os valores.</small></div>
      </aside>
    </div>
  </>;
}

function MonthlyForm({ values, onChange, month, setMonth }: { values: FormValues; onChange: (field: FormField, value: string) => void; month: number; setMonth: (month: number) => void }) {
  return <div className="form-body"><div className="form-section-title"><span className="step-index">01</span><div><h3>Rendimentos do mês</h3><p>Valores referentes à competência selecionada.</p></div></div><div className="field-grid">
    <div className="field-wrap"><label htmlFor="reference-month">Mês de referência</label><div className="select-wrap"><select id="reference-month" value={month} onChange={(event) => setMonth(Number(event.target.value))}>{Array.from({ length: 12 }, (_, index) => <option key={index + 1} value={index + 1}>{new Intl.DateTimeFormat("pt-BR", { month: "long" }).format(new Date(2026, index, 1))}</option>)}</select><ChevronDown size={15} /></div></div>
    <MoneyField label="Salário bruto" hint="Rendimentos tributáveis" value={values.rendaBruta} onChange={(value) => onChange("rendaBruta", value)} /><MoneyField label="Contribuição ao INSS" hint="Valor informado; cálculo automático ainda não disponível" value={values.inss} onChange={(value) => onChange("inss", value)} />
    <div className="field-wrap"><label htmlFor="monthly-dependents">Número de dependentes</label><div className="select-wrap"><select id="monthly-dependents" value={values.dependentes} onChange={(event) => onChange("dependentes", event.target.value)}><option value="0">Nenhum dependente</option>{Array.from({ length: 8 }, (_, index) => <option key={index + 1} value={index + 1}>{index + 1} {index === 0 ? "dependente" : "dependentes"}</option>)}</select><ChevronDown size={15} /></div></div>
    <MoneyField label="Outras deduções legais" hint="Pensão ou outra dedução permitida" value={values.outrasDeducoesMensais} onChange={(value) => onChange("outrasDeducoesMensais", value)} />
  </div></div>;
}

function AnnualForm({ year, values, onChange }: { year: number; values: FormValues; onChange: (field: FormField, value: string) => void }) {
  return <div className="form-body"><div className="form-section-title"><span className="step-index">01</span><div><h3>Rendimentos e retenções</h3><p>Exercício {year + 1} · ano-calendário {year}.</p></div></div><div className="field-grid">
    <MoneyField label="Rendimentos tributáveis" hint="Salários, pró-labore e outros" value={values.rendimentosTributaveis} onChange={(value) => onChange("rendimentosTributaveis", value)} /><MoneyField label="Rendimentos isentos" hint="Informe o total anual" value={values.rendimentosIsentos} onChange={(value) => onChange("rendimentosIsentos", value)} /><MoneyField label="Imposto retido na fonte" hint="Conforme seus informes" value={values.irrfRetido} onChange={(value) => onChange("irrfRetido", value)} />
    <div className="field-wrap"><label htmlFor="annual-dependents">Número de dependentes</label><div className="select-wrap"><select id="annual-dependents" value={values.dependentes} onChange={(event) => onChange("dependentes", event.target.value)}><option value="0">Nenhum dependente</option>{Array.from({ length: 8 }, (_, index) => <option key={index + 1} value={index + 1}>{index + 1} {index === 0 ? "dependente" : "dependentes"}</option>)}</select><ChevronDown size={15} /></div></div>
  </div><div className="annual-deductions-title"><HeartPulse size={15} /> Deduções para a declaração anual</div><div className="field-grid annual-grid"><MoneyField label="Despesas médicas" hint="Despesas elegíveis" value={values.despesasMedicas} onChange={(value) => onChange("despesasMedicas", value)} /><MoneyField label="Despesas educacionais" hint="Um beneficiário nesta etapa" value={values.despesasEducacionais} onChange={(value) => onChange("despesasEducacionais", value)} /><MoneyField label="Previdência privada (PGBL)" hint="Indisponível nesta etapa; deixe em branco" value={values.previdenciaPrivada} onChange={(value) => onChange("previdenciaPrivada", value)} /><MoneyField label="Outras deduções" hint="Conforme a legislação" value={values.outrasDeducoesAnuais} onChange={(value) => onChange("outrasDeducoesAnuais", value)} /></div></div>;
}

function MoneyField({ label, hint, value, onChange }: { label: string; hint: string; value: string; onChange: (value: string) => void }) {
  return <div className="field-wrap"><label>{label}</label><div className="money-input"><span>R$</span><input inputMode="decimal" placeholder="0,00" aria-label={label} value={value} onChange={(event) => onChange(event.target.value)} /></div><small>{hint}</small></div>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong></div>;
}

function SummaryRow({ label, value, strong = false }: { label: string; value: string; strong?: boolean }) {
  return <div className={`summary-row ${strong ? "summary-row-strong" : ""}`}><span>{label}</span><strong>{value}</strong></div>;
}

function RateTable({ table }: { table: TaxTable | null }) {
  if (!table) return <div className="table-period">Tabela indisponível para este período.</div>;
  return <div className="rate-table-wrap"><table className="rate-table"><thead><tr><th>Base de cálculo</th><th>Alíquota</th><th>Dedução</th></tr></thead><tbody>
    {table.faixas.map((band, index) => {
      const previousLimit = index === 0 ? 0 : Number(table.faixas[index - 1].limite_superior);
      const range = band.limite_superior === null ? `Acima de ${money.format(previousLimit)}` : index === 0 ? `Até ${money.format(Number(band.limite_superior))}` : `${money.format(previousLimit + 0.01)} – ${money.format(Number(band.limite_superior))}`;
      return <tr key={index}><td>{range}</td><td>{percentages.format(Number(band.aliquota))}</td><td>{Number(band.deducao) === 0 ? "—" : money.format(Number(band.deducao))}</td></tr>;
    })}
  </tbody></table><div className="table-period"><CalendarDays size={12} /> Vigência desde {formatDate(table.vigencia_inicio)}</div></div>;
}

function SecondaryPage({ section, year, tables, onOpenCalculator }: { section: Exclude<Section, "calculator">; year: number; tables: TaxTablesResponse | null; onOpenCalculator: () => void }) {
  const content = sectionCopy[section];
  const Icon = content.icon;
  const monthlyTables = Object.entries(tables?.mensais ?? {}).filter(([key]) => key.startsWith(String(year))).map(([key, table]) => ({ key, table, periodicity: "mensal" }));
  const annualTable = tables?.anuais[String(year)];
  const periodTables = annualTable ? [...monthlyTables, { key: String(year), table: annualTable, periodicity: "anual" }] : monthlyTables;
  return <div className="secondary-page">
    <div className="page-heading"><div><div className="eyebrow"><span className="eyebrow-dot" /> IRPF BRASIL</div><h1>{content.title}</h1><p>{content.subtitle}</p></div><div className="heading-tag"><Icon size={15} /> {year}</div></div>
    {section === "rules" && <div className="rules-list">{periodTables.map(({ key, table, periodicity }) => <div className="panel rules-period" key={`${periodicity}-${key}`}><div className="rules-period-heading"><div className="panel-title-icon"><Landmark size={18} /></div><div><h2>Tabela {periodicity} · {key.replaceAll("-", " ")}</h2><p>Vigência desde {formatDate(table.vigencia_inicio)}{table.vigencia_fim ? ` até ${formatDate(table.vigencia_fim)}` : " · vigente"}</p></div></div><RateTable table={table} /><a className="source-link" href={sourceUrl(table.fonte)} target="_blank" rel="noreferrer">Fonte oficial cadastrada <ArrowUpRight size={14} /></a></div>)}</div>}
    {section === "deductions" && <div className="feature-grid"><FeatureCard icon={Check} title="Deduções legais" text="Informe valores permitidos, como dependentes e outras deduções. A comparação será calculada com as regras do período." tag="Modalidade legal" /><FeatureCard icon={Sparkles} title="Desconto simplificado" text="A interface está preparada para comparar o desconto simplificado com as deduções legais, sem somar as modalidades." tag="Modalidade simplificada" /><div className="panel wide-note"><Info size={17} /><p>Os limites e a vantagem de cada modalidade serão apresentados quando os cálculos forem conectados.</p></div></div>}
    {section === "updates" && <div className="update-layout"><div className="panel update-status-panel"><span className="large-update-icon"><RefreshCw size={22} /></span><div><span className="review-chip"><span /> Fluxo com revisão humana</span><h2>Atualização automática ainda não está habilitada</h2><p>As regras atuais são carregadas de um arquivo versionado no projeto. Antes de publicar uma mudança, a fonte oficial e os cálculos precisam ser conferidos e aprovados.</p></div></div><div className="panel update-source-panel"><h2>Fontes para conferência</h2><a href="https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/tabelas" target="_blank" rel="noreferrer"><Landmark size={16} /> Tabelas da Receita Federal <ArrowUpRight size={14} /></a><a href="https://www.planalto.gov.br/" target="_blank" rel="noreferrer"><FileText size={16} /> Legislação Federal <ArrowUpRight size={14} /></a><div className="source-disclaimer"><ShieldCheck size={15} /> Nenhuma alteração é aplicada automaticamente.</div></div></div>}
    {section === "history" && <div className="panel empty-state"><div className="empty-icon"><Clock3 size={22} /></div><h2>Nenhuma simulação salva</h2><p>O histórico aparecerá aqui quando salvar simulações for implementado. Seus dados não são armazenados nesta etapa.</p><button className="primary-button" onClick={onOpenCalculator}><Calculator size={15} /> Ir para a calculadora</button></div>}
    {section === "about" && <div className="about-grid"><div className="panel about-lead"><span className="about-mark"><Landmark size={23} /></span><h2>Informação tributária com contexto.</h2><p>Este projeto organiza tabelas por período de vigência e registra as fontes utilizadas. O resultado final deve ser tratado como estimativa e conferido nas publicações oficiais.</p><div className="about-points"><span><Check size={14} /> Valores monetários com Decimal no motor Python</span><span><Check size={14} /> Tabelas tributárias em JSON versionado</span><span><Check size={14} /> Revisão humana antes de atualizar regras</span></div></div><div className="panel about-limitations"><h2>Escopo atual</h2><p>Os cálculos mensal e anual estão conectados à API local. INSS automático, PGBL, histórico e verificação periódica de fontes ainda não estão disponíveis.</p><button className="text-link" onClick={onOpenCalculator}>Voltar à calculadora <ChevronRight size={14} /></button></div></div>}
  </div>;
}

function FeatureCard({ icon: Icon, title, text, tag }: { icon: LucideIcon; title: string; text: string; tag: string }) {
  return <div className="panel feature-card"><span className="feature-icon"><Icon size={18} /></span><span className="feature-tag">{tag}</span><h2>{title}</h2><p>{text}</p><span className="feature-pending"><ArrowDownRight size={14} /> Aguardando integração de cálculo</span></div>;
}

function sourceUrl(source: string) {
  return source.match(/https?:\/\/\S+/)?.[0] ?? "https://www.gov.br/receitafederal";
}

function normalizeMoney(rawValue: string, label: string, required = false) {
  const raw = rawValue.trim().replace(/^R\$\s*/, "").replace(/\s/g, "");
  if (!raw) {
    if (required) throw new Error(`Informe ${label.toLowerCase()}.`);
    return "0.00";
  }
  let normalized = raw;
  if (normalized.includes(",")) normalized = normalized.replace(/\./g, "").replace(",", ".");
  else if (/^\d{1,3}(\.\d{3})+$/.test(normalized)) normalized = normalized.replace(/\./g, "");
  if (normalized.startsWith(".")) normalized = `0${normalized}`;
  if (!/^\d+(\.\d{1,2})?$/.test(normalized)) throw new Error(`${label} deve ser um valor não negativo com até duas casas decimais.`);
  const [whole, fraction = ""] = normalized.split(".");
  if (whole.length > 14) throw new Error(`${label} está acima do limite aceito.`);
  return `${whole}.${fraction.padEnd(2, "0")}`;
}

function parseDependents(value: string) {
  const count = Number(value);
  if (!Number.isInteger(count) || count < 0) throw new Error("Informe uma quantidade válida de dependentes.");
  return count;
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Ocorreu um erro inesperado ao calcular.";
}

function asNumber(value: unknown) {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function currencyText(value: unknown) {
  if (value === null || value === undefined || value === "") return "—";
  const number = Number(value);
  return Number.isFinite(number) ? money.format(number) : String(value);
}

function percentageText(value: unknown) {
  if (value === null || value === undefined || value === "") return "—";
  const number = Number(value);
  return Number.isFinite(number) ? percentages.format(number) : String(value);
}

function getScenarioTax(scenario: Record<string, unknown> | undefined, mode: Mode) {
  return scenario?.[mode === "monthly" ? "imposto" : "imposto_devido"];
}

function MemoryRow({ label, value }: { label: string; value: unknown }) {
  const formatted = value && typeof value === "object"
    ? Object.entries(value).map(([key, amount]) => `${key.replaceAll("_", " ")}: ${currencyText(amount)}`).join(" · ")
    : String(value ?? "—");
  return <SummaryRow label={label} value={formatted} />;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC", month: "2-digit", year: "numeric" }).format(new Date(`${value}T00:00:00Z`));
}

export default App;
