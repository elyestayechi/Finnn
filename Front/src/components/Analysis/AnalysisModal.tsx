// AnalysisModal.tsx - Corrected version
import { useState } from 'react';
import { X, Upload, Search, HelpCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { createAnalysis } from '@/lib/api';

interface AnalysisData {
  loan_id: string;
  external_id: string;
  notes: string;
}

interface AnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAnalysisStarted: (analysisId: string) => void;
}

export default function AnalysisModal({ isOpen, onClose, onAnalysisStarted }: AnalysisModalProps) {
  const [loanId, setLoanId] = useState('');
  const [externalId, setExternalId] = useState('');
  const [notes, setNotes] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loanId.trim() || !externalId.trim()) return;

    setIsLoading(true);
    
    try {
      const loanData = {
        loan_id: loanId.trim(),
        external_id: externalId.trim(),
        notes
      };
      
      const response = await createAnalysis(loanData);
      onAnalysisStarted(response.analysis_id);
      onClose();
      
      // Reset form
      setLoanId('');
      setExternalId('');
      setNotes('');
    } catch (error) {
      console.error('Failed to start analysis:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white max-w-md p-5">
        <DialogHeader className="mb-4">
          <DialogTitle className="text-lg font-semibold">New Loan Analysis</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Loan ID Field */}
          <div className="space-y-2">
            <Label htmlFor="loan-id" className="text-sm font-medium text-gray-900 dark:text-white">
              Loan ID *
            </Label>
            <Input
              id="loan-id"
              value={loanId}
              onChange={(e) => setLoanId(e.target.value)}
              placeholder="e.g., 33415"
              className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:border-blue-500 dark:focus:border-blue-400 text-sm"
              required
            />
          </div>

          {/* External ID Field */}
          <div className="space-y-2">
            <Label htmlFor="external-id" className="text-sm font-medium text-gray-900 dark:text-white">
              External ID *
            </Label>
            <Input
              id="external-id"
              value={externalId}
              onChange={(e) => setExternalId(e.target.value)}
              placeholder="e.g., 33421"
              className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:border-blue-500 dark:focus:border-blue-400 text-sm"
              required
            />
          </div>

          {/* Notes */}
          <div className="space-y-2">
            <Label htmlFor="notes" className="text-sm font-medium text-gray-900 dark:text-white">
              Analysis Notes (Optional)
            </Label>
            <Textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add any specific requirements or notes for this analysis..."
              className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:border-blue-500 dark:focus:border-blue-400 min-h-[80px] text-sm"
              rows={3}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-3 pt-4">
            <Button
              type="button"
              onClick={onClose}
              variant="outline"
              className="flex-1 bg-transparent border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!loanId.trim() || !externalId.trim() || isLoading}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm"
            >
              {isLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>Starting...</span>
                </div>
              ) : (
                'Start Analysis'
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}