const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const message =
      typeof data === "object" && data !== null && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : "Request failed";
    throw new ApiError(message, response.status);
  }

  return data as T;
}

function authHeaders(accessToken: string): HeadersInit {
  return {
    Authorization: `Bearer ${accessToken}`,
    "Content-Type": "application/json",
  };
}

export type User = {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
};

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type Category = {
  id: number;
  name: string;
  slug: string | null;
  type: "income" | "expense";
  color: string;
  user_id: number | null;
};

export type Transaction = {
  id: number;
  category_id: number;
  amount: string;
  type: "income" | "expense";
  description: string | null;
  transaction_date: string;
  created_at: string;
  category: Category;
};

export type SummaryStats = {
  balance: string;
  month_income: string;
  month_expenses: string;
  month_savings: string;
};

export type CategoryBreakdown = {
  category_id: number;
  category_name: string;
  category_slug: string | null;
  color: string;
  amount: string;
};

export type MonthlyTrend = {
  month: string;
  income: string;
  expenses: string;
};

export type BalanceTrend = {
  month: string;
  balance: string;
};

export type BudgetProgress = {
  id: number;
  category_id: number;
  category_name: string;
  category_slug: string | null;
  color: string;
  budget_amount: string;
  spent_amount: string;
  remaining_amount: string;
  usage_percent: string;
};

type PeriodParams = {
  month: number;
  year: number;
};

function periodQuery(params: PeriodParams): string {
  return `month=${params.month}&year=${params.year}`;
}

export async function registerUser(payload: {
  email: string;
  password: string;
  full_name?: string;
}): Promise<User> {
  const response = await fetch(`${API_URL}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  return parseResponse<User>(response);
}

export async function loginUser(payload: {
  email: string;
  password: string;
}): Promise<TokenPair> {
  const response = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  return parseResponse<TokenPair>(response);
}

export async function getCurrentUser(accessToken: string): Promise<User> {
  const response = await fetch(`${API_URL}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  return parseResponse<User>(response);
}

export async function getCategories(
  accessToken: string,
  type: "income" | "expense"
): Promise<Category[]> {
  const response = await fetch(`${API_URL}/api/v1/finance/categories?type=${type}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  return parseResponse<Category[]>(response);
}

export async function createCategory(
  accessToken: string,
  payload: {
    name: string;
    type: "income" | "expense";
    color?: string;
  }
): Promise<Category> {
  const response = await fetch(`${API_URL}/api/v1/finance/categories`, {
    method: "POST",
    headers: authHeaders(accessToken),
    body: JSON.stringify(payload),
  });

  return parseResponse<Category>(response);
}

export async function deleteCategory(accessToken: string, id: number): Promise<void> {
  const response = await fetch(`${API_URL}/api/v1/finance/categories/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  if (!response.ok) {
    await parseResponse(response);
  }
}

export async function getTransactions(
  accessToken: string,
  period?: PeriodParams
): Promise<Transaction[]> {
  const query = period ? `?${periodQuery(period)}` : "";
  const response = await fetch(`${API_URL}/api/v1/finance/transactions${query}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  return parseResponse<Transaction[]>(response);
}

export async function createTransaction(
  accessToken: string,
  payload: {
    category_id: number;
    amount: number;
    type: "income" | "expense";
    description?: string;
    transaction_date: string;
  }
): Promise<Transaction> {
  const response = await fetch(`${API_URL}/api/v1/finance/transactions`, {
    method: "POST",
    headers: authHeaders(accessToken),
    body: JSON.stringify(payload),
  });

  return parseResponse<Transaction>(response);
}

export async function deleteTransaction(accessToken: string, id: number): Promise<void> {
  const response = await fetch(`${API_URL}/api/v1/finance/transactions/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  if (!response.ok) {
    await parseResponse(response);
  }
}

export async function getSummary(
  accessToken: string,
  period?: PeriodParams
): Promise<SummaryStats> {
  const query = period ? `?${periodQuery(period)}` : "";
  const response = await fetch(`${API_URL}/api/v1/finance/analytics/summary${query}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  return parseResponse<SummaryStats>(response);
}

export async function getSpendingByCategory(
  accessToken: string,
  period?: PeriodParams
): Promise<CategoryBreakdown[]> {
  const query = period ? `?${periodQuery(period)}` : "";
  const response = await fetch(
    `${API_URL}/api/v1/finance/analytics/spending-by-category${query}`,
    {
      headers: { Authorization: `Bearer ${accessToken}` },
    }
  );

  return parseResponse<CategoryBreakdown[]>(response);
}

export async function getMonthlyTrend(
  accessToken: string,
  period?: PeriodParams
): Promise<MonthlyTrend[]> {
  const query = period ? `?months=6&${periodQuery(period)}` : "?months=6";
  const response = await fetch(`${API_URL}/api/v1/finance/analytics/monthly-trend${query}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  return parseResponse<MonthlyTrend[]>(response);
}

export async function getBalanceTrend(
  accessToken: string,
  period?: PeriodParams
): Promise<BalanceTrend[]> {
  const query = period ? `?months=6&${periodQuery(period)}` : "?months=6";
  const response = await fetch(`${API_URL}/api/v1/finance/analytics/balance-trend${query}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  return parseResponse<BalanceTrend[]>(response);
}

export async function getBudgets(
  accessToken: string,
  period: PeriodParams
): Promise<BudgetProgress[]> {
  const response = await fetch(`${API_URL}/api/v1/finance/budgets?${periodQuery(period)}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  return parseResponse<BudgetProgress[]>(response);
}

export async function upsertBudget(
  accessToken: string,
  payload: {
    category_id: number;
    month: number;
    year: number;
    amount: number;
  }
): Promise<BudgetProgress> {
  const response = await fetch(`${API_URL}/api/v1/finance/budgets`, {
    method: "PUT",
    headers: authHeaders(accessToken),
    body: JSON.stringify(payload),
  });

  return parseResponse<BudgetProgress>(response);
}

export type AiStatus = {
  ai_enabled: boolean;
  ollama_available: boolean;
  qdrant_available: boolean;
  model: string;
};

export type ChatResponse = {
  reply: string;
  model: string;
  used_tools: string[];
  used_rag: boolean;
};

export async function getAiStatus(): Promise<AiStatus> {
  const response = await fetch(`${API_URL}/api/v1/ai/status`);
  return parseResponse<AiStatus>(response);
}

export async function sendAiChat(
  accessToken: string,
  message: string,
  locale: "ro" | "en" = "ro"
): Promise<ChatResponse> {
  const response = await fetch(`${API_URL}/api/v1/ai/chat`, {
    method: "POST",
    headers: authHeaders(accessToken),
    body: JSON.stringify({ message, locale }),
  });

  return parseResponse<ChatResponse>(response);
}
