const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

export interface UploadResponse {
  success: boolean;
  data?: {
    table_name: string;
    row_count: number;
    columns: string[];
    text_column?: string;
  };
  error?: string;
}

export interface AskResponse {
  success: boolean;
  data?: {
    answer: string;
    query_type?: string;
    sql_query?: string;
    execution_time?: number;
  };
  error?: string;
}

export interface SchemaResponse {
  success: boolean;
  data?: {
    table_name: string;
    columns: Array<{
      name: string;
      type: string;
      sample_values?: any[];
    }>;
    row_count: number;
  };
  error?: string;
}

export const api = {
  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: "POST",
      body: formData,
    });

    return response.json();
  },

  async ask(question: string): Promise<AskResponse> {
    const response = await fetch(`${API_BASE_URL}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });

    return response.json();
  },

  async getSchema(): Promise<SchemaResponse> {
    const response = await fetch(`${API_BASE_URL}/schema`);
    return response.json();
  },

  async askStream(question: string): Promise<ReadableStream<Uint8Array>> {
    const response = await fetch(`${API_BASE_URL}/ask_stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });

    if (!response.body) {
      throw new Error("No response body");
    }

    return response.body;
  },
};
