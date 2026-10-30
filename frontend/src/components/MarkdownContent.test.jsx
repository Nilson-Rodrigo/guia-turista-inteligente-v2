// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import MarkdownContent from "./MarkdownContent";

it("renderiza Markdown e remove HTML fornecido pelo modelo", () => {
  render(
    <MarkdownContent>
      {"# Título\n\n- **Atração**\n- *Gastronomia*\n\n<script>alert(1)</script>"}
    </MarkdownContent>,
  );

  expect(screen.getByRole("heading", { name: "Título" })).toBeTruthy();
  expect(screen.getByText("Atração").tagName).toBe("STRONG");
  expect(screen.getByText("Gastronomia").tagName).toBe("EM");
  expect(document.querySelector("script")).toBeNull();
});