
import React, { useState, useEffect } from 'react';
import { billingAPI } from '../services/api';
import './Dashboard.css'; // Reusing some base styles

export default function BillingView() {
  const [categories, setCategories] = useState<any[]>([]);
  const [formData, setFormData] = useState({
    consumer_type: 'A-1',
    units: 0,
    peak_units: 0,
    offpeak_units: 0,
    sanctioned_load: 1,
    phase: 1,
    is_protected: false
  });
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const cats = await billingAPI.getCategories();
      setCategories(cats);
    } catch (err) {
      console.error('Failed to load categories');
    }
  };

  const handleEstimate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await billingAPI.estimate(formData);
      setResult(res);
    } catch (err: any) {
      setError('Failed to calculate estimate. Please check your inputs.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-container">
      <h1 className="text-3xl font-bold mb-6" style={{ color: 'var(--color-accent-primary)' }}>Electricity Bill Estimation (FESCO)</h1>
      <p className="mb-8" style={{ color: 'var(--color-text-secondary)' }}>Calculate your estimated monthly bill based on current FESCO tariff slabs.</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Form */}
        <div className="bg-[var(--color-bg-card)] p-6 rounded-xl border border-[var(--color-border-default)] shadow-lg">
          <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>Estimation Parameters</h2>
          <form onSubmit={handleEstimate} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex flex-col">
                <label className="text-sm mb-1" style={{ color: 'var(--color-text-secondary)' }}>Consumer Category</label>
                <select 
                  className="bg-[var(--color-bg-input)] border border-[var(--color-border-default)] p-2 rounded text-[var(--color-text-primary)] focus:outline-none"
                  value={formData.consumer_type}
                  onChange={(e) => setFormData({...formData, consumer_type: e.target.value})}
                >
                  {categories.map(c => <option key={c.id} value={c.id}>{c.name} ({c.id})</option>)}
                </select>
              </div>

              <div className="flex flex-col">
                <label className="text-sm mb-1" style={{ color: 'var(--color-text-secondary)' }}>Phase Type</label>
                <select 
                  className="bg-[var(--color-bg-input)] border border-[var(--color-border-default)] p-2 rounded text-[var(--color-text-primary)] focus:outline-none"
                  value={formData.phase}
                  onChange={(e) => setFormData({...formData, phase: parseInt(e.target.value)})}
                >
                  <option value={1}>Single Phase</option>
                  <option value={3}>Three Phase</option>
                </select>
              </div>
            </div>

            <div className="flex flex-col">
              <label className="text-sm mb-1" style={{ color: 'var(--color-text-secondary)' }}>Total Units Consumed (kWh)</label>
              <input 
                type="number" 
                className="bg-[var(--color-bg-input)] border border-[var(--color-border-default)] p-2 rounded text-[var(--color-text-primary)] focus:outline-none"
                value={formData.units}
                onChange={(e) => setFormData({...formData, units: parseFloat(e.target.value)})}
              />
            </div>

            {formData.consumer_type === 'A-1' && (
              <div className="flex items-center space-x-2 py-2">
                <input 
                  type="checkbox" 
                  id="is_protected"
                  checked={formData.is_protected}
                  onChange={(e) => setFormData({...formData, is_protected: e.target.checked})}
                  className="w-4 h-4" style={{ accentColor: 'var(--color-success)' }}
                />
                <label htmlFor="is_protected" className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>Protected Consumer (Usage consistently &lt; 200 units)</label>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
               <div className="flex flex-col">
                <label className="text-sm mb-1" style={{ color: 'var(--color-text-secondary)' }}>Sanctioned Load (kW)</label>
                <input 
                  type="number" 
                  step="0.1"
                  className="bg-[var(--color-bg-input)] border border-[var(--color-border-default)] p-2 rounded text-[var(--color-text-primary)] focus:outline-none"
                  value={formData.sanctioned_load}
                  onChange={(e) => setFormData({...formData, sanctioned_load: parseFloat(e.target.value)})}
                />
              </div>
            </div>

            {(formData.sanctioned_load >= 5 || formData.consumer_type === 'A-2') && (
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col">
                  <label className="text-sm mb-1" style={{ color: 'var(--color-text-secondary)' }}>Peak Units</label>
                  <input 
                    type="number" 
                    className="bg-[var(--color-bg-input)] border border-[var(--color-border-default)] p-2 rounded text-[var(--color-text-primary)] focus:outline-none"
                    value={formData.peak_units}
                    onChange={(e) => setFormData({...formData, peak_units: parseFloat(e.target.value)})}
                  />
                </div>
                <div className="flex flex-col">
                  <label className="text-sm mb-1" style={{ color: 'var(--color-text-secondary)' }}>Off-Peak Units</label>
                  <input 
                    type="number" 
                    className="bg-[var(--color-bg-input)] border border-[var(--color-border-default)] p-2 rounded text-[var(--color-text-primary)] focus:outline-none"
                    value={formData.offpeak_units}
                    onChange={(e) => setFormData({...formData, offpeak_units: parseFloat(e.target.value)})}
                  />
                </div>
              </div>
            )}

            <button 
              type="submit"
              disabled={loading}
              className="w-full text-black font-bold py-3 rounded-lg transition-all shadow-lg"
              style={{ backgroundColor: 'var(--color-accent-primary)', boxShadow: '0 10px 30px rgba(6,182,212,0.06)' }}
            >
              {loading ? 'Calculating...' : 'Generate Estimate'}
            </button>
          </form>
          {error && <p className="text-red-500 mt-4 text-sm font-medium">{error}</p>}
        </div>

        {/* Results Section */}
        <div className="p-6 rounded-xl shadow-lg flex flex-col" style={{ backgroundColor: 'var(--color-bg-card)', border: '1px solid var(--color-border-default)' }}>
          {result ? (
            <>
              <h2 className="text-xl font-semibold mb-2" style={{ color: 'var(--color-text-primary)' }}>Bill Summary</h2>
              <p className="text-sm mb-6" style={{ color: 'var(--color-text-secondary)' }}>Category: <span style={{ color: 'var(--color-accent-primary)' }}>{result.consumer_type}</span></p>
              
              <div className="text-center py-6 rounded-lg mb-8" style={{ backgroundColor: 'var(--color-bg-input)', border: '1px solid var(--color-border-default)' }}>
                <p className="text-sm uppercase tracking-wider" style={{ color: 'var(--color-text-secondary)' }}>Estimated Total Bill</p>
                <h3 className="text-5xl font-bold mt-2" style={{ color: 'var(--color-accent-primary)' }}>Rs. {result.total_bill.toLocaleString()}</h3>
                <p className="text-xs mt-2" style={{ color: 'var(--color-text-secondary)' }}>*Inclusive of energy & fixed charges</p>
              </div>

              <div className="space-y-4 flex-1">
                <h4 className="text-sm font-bold border-b pb-1" style={{ color: 'var(--color-text-secondary)', borderColor: 'var(--color-border-default)' }}>Cost Breakdown</h4>
                <div className="space-y-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                  {result.breakdown.map((item: any, idx: number) => (
                    <div key={idx} className="flex justify-between text-sm">
                      <span style={{ color: 'var(--color-text-secondary)' }}>{item.slab} {item.units > 0 ? `(${item.units} units @ ${item.rate})` : ''}</span>
                      <span style={{ color: 'var(--color-text-primary)', fontWeight: 600 }}>Rs. {item.cost.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
                
                <div className="flex justify-between pt-4" style={{ borderTop: '1px solid var(--color-border-default)' }}>
                  <span style={{ color: 'var(--color-text-secondary)', fontWeight: 600 }}>Fixed Charges</span>
                  <span style={{ color: 'var(--color-text-primary)', fontWeight: 700 }}>Rs. {result.fixed_charges.toLocaleString()}</span>
                </div>
              </div>

              {/* Optimization Suggestion */}
              <div className="mt-8 p-4 bg-green-900/20 border border-green-500/30 rounded-lg">
                 <div className="flex items-start space-x-3">
                    <div className="bg-green-500 rounded-full p-1 mt-1">
                      <svg className="w-4 h-4 text-black" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div>
                      <h5 className="text-green-500 font-bold text-sm">AI Optimization Hint</h5>
                      <p className="text-gray-300 text-xs mt-1 leading-relaxed">{result.optimization_suggestion}</p>
                    </div>
                 </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center opacity-30">
               <svg className="w-24 h-24 text-gray-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
               </svg>
               <p className="text-gray-400">Fill in the details to generate your energy bill estimation.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
