import { MessageCircle } from "lucide-react";

interface ChatButtonProps {
  isOpen: boolean;
  onClick: () => void;
}

export default function ChatButton({ isOpen, onClick }: ChatButtonProps) {
  return (
    <button
      onClick={onClick}
      className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-shield-accent hover:bg-orange-600 text-white shadow-lg flex items-center justify-center transition-all duration-200 hover:scale-105"
      aria-label={isOpen ? "Close chat" : "Open chat"}
    >
      {isOpen ? (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      ) : (
        <>
          <MessageCircle size={24} />
          <span className="absolute top-1 right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse" />
        </>
      )}
    </button>
  );
}
