import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-screen bg-gray-50 dark:bg-gray-900 text-white p-4 text-center">
          <div className="bg-gray-800 p-8 rounded-2xl shadow-neon-green border border-green-500/30 max-w-md w-full">
            <h1 className="text-4xl font-bold text-green-500 mb-4">Oops!</h1>
            <p className="text-gray-400 mb-6 text-lg">
              Something went wrong. The application encountered an unexpected error.
            </p>
            <div className="bg-black/50 p-4 rounded-lg mb-6 text-left overflow-auto max-h-40">
              <code className="text-red-400 text-sm">
                {this.state.error?.toString()}
              </code>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-green-500 hover:bg-green-600 text-black font-bold py-3 px-6 rounded-xl transition-all active:scale-95 shadow-lg shadow-green-500/20"
            >
              Reload Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
