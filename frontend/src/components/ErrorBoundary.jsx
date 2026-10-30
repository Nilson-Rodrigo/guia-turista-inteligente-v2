import { Component } from "react";

export default class ErrorBoundary extends Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return <section className="error-boundary"><h2>Não foi possível renderizar esta seção.</h2><button className="primary-button" onClick={() => window.location.reload()}>Recarregar</button></section>;
    }
    return this.props.children;
  }
}
