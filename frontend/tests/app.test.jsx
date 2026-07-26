import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import App from "../app/page";


test("renders the login experience and demo accounts", () => {
  render(<App />);
  expect(screen.getByText("Every journey.")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "client" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "admin" })).toBeInTheDocument();
});


test("demo selector changes credentials", () => {
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "admin" }));
  expect(screen.getByDisplayValue("admin@voyageai.demo")).toBeInTheDocument();
});


test("successful login renders client dashboard", async () => {
  const session = {
    access_token: "test-token",
    token_type: "bearer",
    user: {
      id: 3,
      email: "client@acme.demo",
      full_name: "Aarav Sharma",
      role: "client",
      phone: "",
      job_title: "",
      preferences: {},
      active: true,
      organization_id: 1,
    },
  };
  vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce({
      ok: true,
      json: async () => session,
    })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    });
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
  await waitFor(() =>
    expect(screen.getByText("Good to see you, Aarav.")).toBeInTheDocument()
  );
  expect(localStorage.getItem("voyage-session")).toContain("test-token");
});
