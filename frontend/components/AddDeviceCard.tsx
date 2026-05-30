import React, { useState } from 'react';
import { DEVICE_TEMPLATES, customTemplateDefaults, DeviceTemplate } from './DeviceTemplates';
import { Device, DeviceStatus } from '../types';

interface AddDeviceCardProps {
  onAdd: (name: string, template: DeviceTemplate, customDetails?: {
    power: number;
    maxPower: number;
    adjustable: boolean;
  }) => void;
}

const AddDeviceCard: React.FC<AddDeviceCardProps> = ({ onAdd }) => {
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>(DEVICE_TEMPLATES[0].id);
  const [customName, setCustomName] = useState('');
  const [customPower, setCustomPower] = useState(customTemplateDefaults.power);
  const [customMaxPower, setCustomMaxPower] = useState(customTemplateDefaults.maxPower);
  const [customAdjustable, setCustomAdjustable] = useState(customTemplateDefaults.isAdjustable);
  const [formError, setFormError] = useState('');

  const selectedTemplate = DEVICE_TEMPLATES.find(template => template.id === selectedTemplateId) ?? DEVICE_TEMPLATES[0];
  const isCustomTemplate = selectedTemplate.id === 'custom';

  const handleTemplateChange = (templateId: string) => {
    setSelectedTemplateId(templateId);
    setFormError('');
    if (templateId !== 'custom') {
      setCustomName('');
    } else {
      setCustomPower(customTemplateDefaults.power);
      setCustomMaxPower(customTemplateDefaults.maxPower);
      setCustomAdjustable(customTemplateDefaults.isAdjustable);
    }
  };

  const handleAddClick = () => {
    const effectiveName = (customName || selectedTemplate.blueprint.name).trim();
    if (!effectiveName) {
      setFormError('Please provide a device name.');
      return;
    }

    if (selectedTemplateId === 'custom') {
      onAdd(effectiveName, selectedTemplate, {
        power: customPower,
        maxPower: customMaxPower,
        adjustable: customAdjustable
      });
    } else {
      onAdd(effectiveName, selectedTemplate);
    }

    setCustomName('');
    setFormError('');
  };

  return (
    <div className="rounded-2xl p-6 space-y-4 shadow-sm" style={{ backgroundColor: 'var(--color-bg-card)', border: '1px solid var(--color-border-default)' }}>
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-wide" style={{ color: 'var(--color-text-secondary)' }}>Household library</p>
          <h2 className="text-xl font-semibold" style={{ color: 'var(--color-text-primary)' }}>Add a device</h2>
        </div>
        <div className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
          Mirror your actual home by selecting common appliances or defining a custom profile.
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <label htmlFor="device-template" className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>Template</label>
          <select
            id="device-template"
            className="w-full rounded-lg px-3 py-2 text-sm focus:outline-none"
            style={{ backgroundColor: 'var(--color-bg-input)', border: '1px solid var(--color-border-default)', color: 'var(--color-text-primary)' }}
            value={selectedTemplateId}
            onChange={(e) => handleTemplateChange(e.target.value)}
          >
            {DEVICE_TEMPLATES.map(template => (
              <option key={template.id} value={template.id}>
                {template.label}
              </option>
            ))}
          </select>
          <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{selectedTemplate.description}</p>
        </div>
        <div className="space-y-2">
          <label htmlFor="device-name" className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>Display name</label>
          <input
            id="device-name"
            type="text"
            value={customName}
            placeholder={selectedTemplate.blueprint.name}
            onChange={(e) => setCustomName(e.target.value)}
            className="w-full rounded-lg px-3 py-2 text-sm focus:outline-none"
            style={{ backgroundColor: 'var(--color-bg-input)', border: '1px solid var(--color-border-default)', color: 'var(--color-text-primary)' }}
          />
        </div>
      </div>
      {isCustomTemplate && (
        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <label className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>Power draw (W)</label>
            <input
              type="range"
              min={0}
              max={3000}
              value={customPower}
              onChange={(e) => setCustomPower(parseInt(e.target.value, 10))}
              className="w-full mt-2"
            />
            <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{customPower} W when active</p>
          </div>
          <div>
            <label className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>Max power (W)</label>
            <input
              type="range"
              min={Math.max(customPower, 100)}
              max={4000}
              value={customMaxPower}
              onChange={(e) => setCustomMaxPower(parseInt(e.target.value, 10))}
              className="w-full mt-2"
            />
            <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{customMaxPower} W ceiling</p>
          </div>
          <div className="flex items-center space-x-3 mt-6 md:mt-8">
            <input
              id="custom-adjustable"
              type="checkbox"
              checked={customAdjustable}
              onChange={(e) => setCustomAdjustable(e.target.checked)}
              className="h-4 w-4"
              style={{ accentColor: 'var(--color-accent-primary)', borderColor: 'var(--color-border-default)' }}
            />
            <label htmlFor="custom-adjustable" className="text-sm" style={{ color: 'var(--color-text-primary)' }}>
              Adjustable via slider
            </label>
          </div>
        </div>
      )}
      {formError && <p className="text-sm" style={{ color: 'var(--color-danger)' }}>{formError}</p>}
      <div className="flex justify-end">
        <button
          onClick={handleAddClick}
          className="inline-flex items-center px-5 py-2 rounded-lg text-sm font-semibold transition-colors"
          style={{ backgroundColor: 'var(--color-accent-primary)', color: 'black' }}
        >
          Add Device
        </button>
      </div>
    </div>
  );
};

export default AddDeviceCard;
