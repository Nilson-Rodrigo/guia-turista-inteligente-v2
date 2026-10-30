// @vitest-environment jsdom
import React from "react";
import { afterEach, it, expect, vi } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import RoteiroForm, { initialForm } from "./RoteiroForm";
import Toast from "./Toast";
afterEach(cleanup);
it("mostra combustão e limites", () => {
  render(
    <RoteiroForm form={initialForm} setForm={() => {}} onSubmit={() => {}} />,
  );
  expect(screen.getByLabelText("Tanque (litros)").value).toBe("50");
  expect(screen.getByLabelText("Passageiros").max).toBe("8");
});
it("mostra bateria elétrica", () => {
  render(
    <RoteiroForm
      form={{ ...initialForm, propulsao: "eletrico" }}
      setForm={() => {}}
      onSubmit={() => {}}
    />,
  );
  expect(screen.getByLabelText("Bateria (kWh)")).toBeTruthy();
  expect(screen.queryByLabelText("Tanque (litros)")).toBeNull();
});
it("bloqueia submissão durante carregamento", () => {
  render(
    <RoteiroForm
      form={initialForm}
      setForm={() => {}}
      loading
      onSubmit={() => {}}
    />,
  );
  expect(screen.getByText("Planejando…").disabled).toBe(true);
});
it("aciona GPS", () => {
  const fn = vi.fn();
  render(
    <RoteiroForm
      form={initialForm}
      setForm={() => {}}
      onGPS={fn}
      onSubmit={() => {}}
    />,
  );
  fireEvent.click(screen.getByText(/Usar GPS/));
  expect(fn).toHaveBeenCalledOnce();
});
it("Toast apresenta mensagem", () => {
  render(<Toast message="Salvo" type="success" />);
  expect(screen.getByText("Salvo")).toBeTruthy();
});
