// [Task]: T061 — Frontend API client for task operations
/**
 * API client for the Backend Service.
 * All requests include X-User-ID header for authentication.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

export interface Task {
  id: string;
  title: string;
  description: string | null;
  status: "pending" | "completed" | "deleted";
  priority: "high" | "medium" | "low";
  due_date: string | null;
  tags: string[];
  recurrence_pattern: "daily" | "weekly" | "monthly" | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  title: string;
  description?: string;
  priority?: "high" | "medium" | "low";
  due_date?: string;
  tags?: string[];
  recurrence_pattern?: "daily" | "weekly" | "monthly";
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  priority?: "high" | "medium" | "low";
  due_date?: string;
  tags?: string[];
}

export interface TaskFilters {
  search?: string;
  priority?: string;
  tag?: string;
  status?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

function buildHeaders(userId: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    "X-User-ID": userId,
  };
}

function buildQueryString(filters: TaskFilters): string {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.priority) params.set("priority", filters.priority);
  if (filters.tag) params.set("tag", filters.tag);
  if (filters.status) params.set("status", filters.status);
  if (filters.sort_by) params.set("sort_by", filters.sort_by);
  if (filters.sort_order) params.set("sort_order", filters.sort_order);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export async function listTasks(
  userId: string,
  filters: TaskFilters = {}
): Promise<Task[]> {
  const qs = buildQueryString(filters);
  const res = await fetch(`${API_BASE}/tasks${qs}`, {
    headers: buildHeaders(userId),
  });
  if (!res.ok) throw new Error(`Failed to list tasks: ${res.status}`);
  return res.json();
}

export async function getTask(taskId: string): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}`);
  if (!res.ok) throw new Error(`Failed to get task: ${res.status}`);
  return res.json();
}

export async function createTask(
  userId: string,
  data: TaskCreate
): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks`, {
    method: "POST",
    headers: buildHeaders(userId),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to create task: ${res.status}`);
  return res.json();
}

export async function updateTask(
  userId: string,
  taskId: string,
  data: TaskUpdate
): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
    method: "PATCH",
    headers: buildHeaders(userId),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to update task: ${res.status}`);
  return res.json();
}

export async function deleteTask(
  userId: string,
  taskId: string
): Promise<void> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
    method: "DELETE",
    headers: buildHeaders(userId),
  });
  if (!res.ok) throw new Error(`Failed to delete task: ${res.status}`);
}

export async function completeTask(
  userId: string,
  taskId: string
): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}/complete`, {
    method: "POST",
    headers: buildHeaders(userId),
  });
  if (!res.ok) throw new Error(`Failed to complete task: ${res.status}`);
  return res.json();
}

export async function updateTags(
  userId: string,
  taskId: string,
  tags: string[]
): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}/tags`, {
    method: "PUT",
    headers: buildHeaders(userId),
    body: JSON.stringify({ tags }),
  });
  if (!res.ok) throw new Error(`Failed to update tags: ${res.status}`);
  return res.json();
}
