import { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { Send, Loader2, Sparkles } from 'lucide-react'
import { useAppStore } from '../hooks/useStore'
import { analyzeData } from '../services/api'
import type { ChatMessage } from '../types'

export function ChatPanel() {
  const { sessionId, chatHistory, isLoading, addMessage, setLoading, setError } = useAppStore()
  const [question, setQuestion] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory])

  useEffect(() => {
    if (!isLoading && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isLoading])

  const handleSend = async () => {
    const q = question.trim()
    if (!q || !sessionId || isLoading) return

    setQuestion('')
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      question: q,
      timestamp: new Date(),
    }
    addMessage(userMsg)
    setLoading(true)
    setError(null)

    try {
      const res = await analyzeData({ session_id: sessionId, question: q })
      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        question: q,
        narrative: res.narrative || undefined,
        recommendation: res.recommendation || undefined,
        chartHtml: res.chart_html || undefined,
        error: res.error || undefined,
        timestamp: new Date(),
      }
      addMessage(assistantMsg)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Lỗi phân tích'
      setError(message)
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        question: q,
        error: message,
        timestamp: new Date(),
      }
      addMessage(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const suggestedQuestions = [
    'Mặt hàng nào bán chạy nhất?',
    'Doanh thu có xu hướng tăng hay giảm?',
    'Khu vực nào có lợi nhuận cao nhất?',
  ]

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {chatHistory.length === 0 && (
          <div className="text-center py-10 animate-fade-in">
            <Sparkles className="w-10 h-10 text-brand-400 mx-auto mb-3" />
            <p className="text-gray-700 font-medium mb-2">Bạn muốn biết điều gì về dữ liệu?</p>
            <p className="text-sm text-gray-500 mb-4">Đặt câu hỏi bằng tiếng Việt tự nhiên</p>
            <div className="flex flex-wrap justify-center gap-2">
              {suggestedQuestions.map((q) => (
                <button
                  key={q}
                  onClick={() => setQuestion(q)}
                  className="px-3 py-1.5 text-sm bg-brand-50 text-brand-700 rounded-full hover:bg-brand-100 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {chatHistory.map((msg) => (
          <div key={msg.id} className={`animate-slide-up ${msg.role === 'user' ? 'flex justify-end' : ''}`}>
            {msg.role === 'user' ? (
              <div className="max-w-[80%] bg-brand-600 text-white rounded-2xl rounded-br-md px-4 py-2.5 shadow-sm">
                <p className="text-sm">{msg.question}</p>
              </div>
            ) : (
              <div className="max-w-[85%] space-y-3">
                <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
                  {msg.error ? (
                    <div className="flex items-start gap-2">
                      <span className="text-red-500 text-lg">⚠️</span>
                      <p className="text-sm text-red-700">{msg.error}</p>
                    </div>
                  ) : (
                    <>
                      {msg.chartHtml && (
                        <div
                          className="chart-container mb-3 -mx-1"
                          dangerouslySetInnerHTML={{ __html: msg.chartHtml }}
                        />
                      )}
                      {msg.narrative && (
                        <div className="prose prose-sm max-w-none text-gray-800 whitespace-pre-wrap leading-relaxed">
                          {msg.narrative}
                        </div>
                      )}
                      {msg.recommendation && (
                        <div className="mt-3 pt-3 border-t border-gray-100">
                          <p className="text-sm text-gray-700">{msg.recommendation}</p>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center gap-2 text-gray-500 animate-fade-in pl-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm">Đang phân tích dữ liệu của bạn...</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="border-t border-gray-200 px-4 py-3 bg-white">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={sessionId ? 'Hỏi về dữ liệu của bạn...' : 'Tải file lên trước để bắt đầu...'}
            disabled={!sessionId || isLoading}
            className="input-field flex-1"
          />
          <button
            onClick={handleSend}
            disabled={!sessionId || !question.trim() || isLoading}
            className="btn-primary px-4"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  )
}
