// [Task]: T064 — Unit tests for TaskFilterBar component
/**
 * Tests for the TaskFilterBar React component.
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import TaskFilterBar, {
  FilterState,
} from "../src/components/TaskFilterBar";

describe("TaskFilterBar", () => {
  const mockOnFilterChange = jest.fn();

  beforeEach(() => {
    mockOnFilterChange.mockClear();
  });

  it("renders all filter controls", () => {
    render(<TaskFilterBar onFilterChange={mockOnFilterChange} />);

    expect(screen.getByLabelText("Search tasks")).toBeInTheDocument();
    expect(screen.getByLabelText("Filter by priority")).toBeInTheDocument();
    expect(screen.getByLabelText("Filter by status")).toBeInTheDocument();
    expect(screen.getByLabelText("Filter by tag")).toBeInTheDocument();
    expect(screen.getByLabelText("Sort by")).toBeInTheDocument();
    expect(screen.getByLabelText("Clear filters")).toBeInTheDocument();
  });

  it("calls onFilterChange when search input changes", () => {
    render(<TaskFilterBar onFilterChange={mockOnFilterChange} />);

    const searchInput = screen.getByLabelText("Search tasks");
    fireEvent.change(searchInput, { target: { value: "buy" } });

    expect(mockOnFilterChange).toHaveBeenCalledWith(
      expect.objectContaining({ search: "buy" })
    );
  });

  it("calls onFilterChange when priority filter changes", () => {
    render(<TaskFilterBar onFilterChange={mockOnFilterChange} />);

    const prioritySelect = screen.getByLabelText("Filter by priority");
    fireEvent.change(prioritySelect, { target: { value: "high" } });

    expect(mockOnFilterChange).toHaveBeenCalledWith(
      expect.objectContaining({ priority: "high" })
    );
  });

  it("renders available tags as options", () => {
    render(
      <TaskFilterBar
        onFilterChange={mockOnFilterChange}
        availableTags={["work", "personal"]}
      />
    );

    const tagSelect = screen.getByLabelText("Filter by tag");
    expect(tagSelect).toContainHTML("work");
    expect(tagSelect).toContainHTML("personal");
  });

  it("toggles sort order on button click", () => {
    render(<TaskFilterBar onFilterChange={mockOnFilterChange} />);

    const sortButton = screen.getByText("DESC");
    fireEvent.click(sortButton);

    expect(mockOnFilterChange).toHaveBeenCalledWith(
      expect.objectContaining({ sortOrder: "asc" })
    );
  });

  it("clears all filters on clear button click", () => {
    render(<TaskFilterBar onFilterChange={mockOnFilterChange} />);

    // Set a filter first
    const searchInput = screen.getByLabelText("Search tasks");
    fireEvent.change(searchInput, { target: { value: "test" } });
    mockOnFilterChange.mockClear();

    // Clear filters
    const clearButton = screen.getByLabelText("Clear filters");
    fireEvent.click(clearButton);

    expect(mockOnFilterChange).toHaveBeenCalledWith(
      expect.objectContaining({
        search: "",
        priority: "",
        tag: "",
        status: "",
        sortBy: "created_at",
        sortOrder: "desc",
      })
    );
  });
});
