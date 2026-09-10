export type ModelTask =
  | 'explain'
  | 'hint'
  | 'interpret_reasoning'
  | 'generate_problem'
  | 'teacher_summary';

export interface ModelRequest {
  task: ModelTask;
  system: string;
  input: string;
  context?: string;
  temperature?: number;
}

export interface ModelResponse {
  text: string;
  provider: string;
  model: string;
}

/**
 * Models are capabilities, not owners of learner state.
 * Implementations may call Gemini, Ollama, Mistral, etc.; the learning engine
 * remains authoritative over mastery, misconceptions and progression.
 */
export interface ModelGateway {
  complete(request: ModelRequest): Promise<ModelResponse>;
}

export class UnconfiguredModelGateway implements ModelGateway {
  async complete(_request: ModelRequest): Promise<ModelResponse> {
    throw new Error('No model gateway is configured for this Vita deployment');
  }
}
