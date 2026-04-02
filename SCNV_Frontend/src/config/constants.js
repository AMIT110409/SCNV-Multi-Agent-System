export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const SUPABASE_URL = 'https://nvdoiirgulzoncuecwdy.supabase.co';
export const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52ZG9paXJndWx6b25jdWVjd2R5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM1ODg3OTgsImV4cCI6MjA4OTE2NDc5OH0.nF30GA2Xc02mg4RzctJs09jNBUWCGn3BhZwdeZHtcFE';
export const STORAGE_KEYS = {
  TOKEN: 'pharma_rag_token',
  ROLE: 'pharma_rag_role',
  EMAIL: 'pharma_rag_email',
};

export const SUPPORTED_FILE_EXTENSIONS = ['.pdf', '.txt', '.md', '.csv', '.doc', '.docx', '.json', '.xlsx'];
