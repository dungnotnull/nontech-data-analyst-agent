import { create } from 'zustand'
import type { UploadResponse, ChatMessage, SchemaInfo } from '../types'

interface AppState {
  sessionId: string | null
  fileName: string | null
  fileSizeMb: number | null
  sheets: string[]
  schemas: Record<string, SchemaInfo>
  chatHistory: ChatMessage[]
  isLoading: boolean
  error: string | null

  setSession: (data: UploadResponse) => void
  addMessage: (msg: ChatMessage) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearSession: () => void
}

export const useAppStore = create<AppState>((set) => ({
  sessionId: null,
  fileName: null,
  fileSizeMb: null,
  sheets: [],
  schemas: {},
  chatHistory: [],
  isLoading: false,
  error: null,

  setSession: (data) =>
    set({
      sessionId: data.session_id,
      fileName: data.file_name,
      fileSizeMb: data.file_size_mb,
      sheets: data.sheets,
      schemas: data.schemas,
    }),

  addMessage: (msg) =>
    set((state) => ({
      chatHistory: [...state.chatHistory, msg],
    })),

  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  clearSession: () =>
    set({
      sessionId: null,
      fileName: null,
      fileSizeMb: null,
      sheets: [],
      schemas: {},
      chatHistory: [],
      error: null,
    }),
}))
