// [Task]: T060 — TaskFilterBar component
/**
 * Filter bar for task list — priority dropdown, tag filter,
 * search input, and sort controls.
 */
"use client";

import React, { useState, useCallback } from "react";

export interface FilterState {
  search: string;
  priority: string;
  tag: string;
  status: string;
  sortBy: string;
  sortOrder: "asc" | "desc";
}

interface TaskFilterBarProps {
  onFilterChange: (filters: FilterState) => void;
  availableTags?: string[];
}

const DEFAULT_FILTERS: FilterState = {
  search: "",
  priority: "",
  tag: "",
  status: "",
  sortBy: "created_at",
  sortOrder: "desc",
};

export default function TaskFilterBar({
  onFilterChange,
  availableTags = [],
}: TaskFilterBarProps) {
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);

  const updateFilter = useCallback(
    (field: keyof FilterState, value: string) => {
      const updated = { ...filters, [field]: value };
      setFilters(updated);
      onFilterChange(updated);
    },
    [filters, onFilterChange]
  );

  const clearFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
    onFilterChange(DEFAULT_FILTERS);
  }, [onFilterChange]);

  return (
    <div className="task-filter-bar" role="search">
      {/* Search input */}
      <input
        type="text"
        placeholder="Search tasks..."
        value={filters.search}
        onChange={(e) => updateFilter("search", e.target.value)}
        className="filter-search"
        aria-label="Search tasks"
      />

      {/* Priority filter */}
      <select
        value={filters.priority}
        onChange={(e) => updateFilter("priority", e.target.value)}
        className="filter-priority"
        aria-label="Filter by priority"
      >
        <option value="">All Priorities</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
      </select>

      {/* Status filter */}
      <select
        value={filters.status}
        onChange={(e) => updateFilter("status", e.target.value)}
        className="filter-status"
        aria-label="Filter by status"
      >
        <option value="">All Statuses</option>
        <option value="pending">Pending</option>
        <option value="completed">Completed</option>
      </select>

      {/* Tag filter */}
      <select
        value={filters.tag}
        onChange={(e) => updateFilter("tag", e.target.value)}
        className="filter-tag"
        aria-label="Filter by tag"
      >
        <option value="">All Tags</option>
        {availableTags.map((tag) => (
          <option key={tag} value={tag}>
            {tag}
          </option>
        ))}
      </select>

      {/* Sort controls */}
      <select
        value={filters.sortBy}
        onChange={(e) => updateFilter("sortBy", e.target.value)}
        className="filter-sort-by"
        aria-label="Sort by"
      >
        <option value="created_at">Date Created</option>
        <option value="priority">Priority</option>
        <option value="due_date">Due Date</option>
        <option value="title">Title</option>
      </select>

      <button
        onClick={() =>
          updateFilter(
            "sortOrder",
            filters.sortOrder === "asc" ? "desc" : "asc"
          )
        }
        className="filter-sort-order"
        aria-label={`Sort ${filters.sortOrder === "asc" ? "descending" : "ascending"}`}
      >
        {filters.sortOrder === "asc" ? "ASC" : "DESC"}
      </button>

      <button
        onClick={clearFilters}
        className="filter-clear"
        aria-label="Clear filters"
      >
        Clear
      </button>
    </div>
  );
}
