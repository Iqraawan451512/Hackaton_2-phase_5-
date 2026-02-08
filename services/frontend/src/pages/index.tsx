// [Task]: T062, T069 — Task list page with filter/sort/search and real-time sync
/**
 * Main task list page — integrates TaskFilterBar with task listing
 * and real-time updates via WebSocket.
 */
"use client";

import React, { useEffect, useState, useCallback } from "react";
import TaskFilterBar, {
  FilterState,
} from "../components/TaskFilterBar";
import { listTasks, Task, TaskFilters } from "../services/api-client";
import {
  useRealtimeUpdates,
  TaskUpdateEvent,
} from "../hooks/useRealtimeUpdates";

// Default user ID for development (replaced by auth in production)
const USER_ID = process.env.NEXT_PUBLIC_USER_ID || "default-user";

export default function HomePage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [availableTags, setAvailableTags] = useState<string[]>([]);

  const fetchTasks = useCallback(async (filters?: FilterState) => {
    setLoading(true);
    setError(null);
    try {
      const apiFilters: TaskFilters = {};
      if (filters) {
        if (filters.search) apiFilters.search = filters.search;
        if (filters.priority) apiFilters.priority = filters.priority;
        if (filters.tag) apiFilters.tag = filters.tag;
        if (filters.status) apiFilters.status = filters.status;
        if (filters.sortBy) apiFilters.sort_by = filters.sortBy;
        if (filters.sortOrder) apiFilters.sort_order = filters.sortOrder;
      }
      const result = await listTasks(USER_ID, apiFilters);
      setTasks(result);

      // Collect unique tags for the filter dropdown
      const tags = new Set<string>();
      result.forEach((t) => t.tags.forEach((tag) => tags.add(tag)));
      setAvailableTags(Array.from(tags).sort());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tasks");
    } finally {
      setLoading(false);
    }
  }, []);

  // Real-time updates via WebSocket
  const handleRealtimeUpdate = useCallback(
    (event: TaskUpdateEvent) => {
      const updatedTask = event.task as unknown as Task;
      setTasks((prev) => {
        if (event.event_type === "task.deleted") {
          return prev.filter((t) => t.id !== event.task_id);
        }
        const idx = prev.findIndex((t) => t.id === event.task_id);
        if (idx >= 0) {
          const next = [...prev];
          next[idx] = updatedTask;
          return next;
        }
        // New task — prepend
        return [updatedTask, ...prev];
      });
    },
    []
  );

  useRealtimeUpdates(handleRealtimeUpdate);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const handleFilterChange = useCallback(
    (filters: FilterState) => {
      fetchTasks(filters);
    },
    [fetchTasks]
  );

  return (
    <main className="task-list-page">
      <h1>Todo Chatbot</h1>

      <TaskFilterBar
        onFilterChange={handleFilterChange}
        availableTags={availableTags}
      />

      {loading && <p>Loading tasks...</p>}
      {error && <p className="error">{error}</p>}

      {!loading && !error && tasks.length === 0 && (
        <p>No tasks found.</p>
      )}

      <ul className="task-list">
        {tasks.map((task) => (
          <li key={task.id} className={`task-item priority-${task.priority}`}>
            <div className="task-header">
              <span className="task-title">{task.title}</span>
              <span className={`task-priority priority-${task.priority}`}>
                {task.priority}
              </span>
              <span className={`task-status status-${task.status}`}>
                {task.status}
              </span>
            </div>
            {task.description && (
              <p className="task-description">{task.description}</p>
            )}
            {task.tags.length > 0 && (
              <div className="task-tags">
                {task.tags.map((tag) => (
                  <span key={tag} className="tag">
                    {tag}
                  </span>
                ))}
              </div>
            )}
            {task.due_date && (
              <span className="task-due-date">
                Due: {new Date(task.due_date).toLocaleDateString()}
              </span>
            )}
          </li>
        ))}
      </ul>
    </main>
  );
}
