import React, { useState } from 'react';
import { X, UploadCloud, CheckCircle2, AlertCircle, FileCode } from 'lucide-react';
import { uploadNetCDF } from '../api/client';

export default function UploadModal({ isOpen, onClose }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setResponse(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const res = await uploadNetCDF(file);
      setResponse(res);
    } catch (err) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 select-none">
      <div className="bg-meteor-900 border border-meteor-700 rounded-xl w-full max-w-lg overflow-hidden shadow-2xl">
        {/* Modal Header */}
        <div className="px-5 py-4 border-b border-meteor-700/70 flex items-center justify-between bg-meteor-950/60">
          <div className="flex items-center space-x-2">
            <UploadCloud className="w-5 h-5 text-cyan-400" />
            <h3 className="text-sm font-bold text-slate-100">Upload NWP Forecast NetCDF Payload</h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 space-y-4">
          <p className="text-xs text-slate-300 leading-relaxed">
            Upload an operational or experimental NetCDF4 file containing gridded meteorological channels
            (<span className="font-mono text-cyan-300">pwat, z500, mslp, vort850, precip</span>) across the South Asian domain (5°N–38°N, 65°E–100°E).
          </p>

          {/* File Input Box */}
          <div className="border-2 border-dashed border-meteor-700 hover:border-cyan-500/60 rounded-xl p-6 text-center transition-colors bg-meteor-950/40">
            <input
              type="file"
              accept=".nc,.netcdf"
              id="netcdf-upload"
              onChange={handleFileChange}
              className="hidden"
            />
            <label htmlFor="netcdf-upload" className="cursor-pointer flex flex-col items-center">
              <FileCode className="w-10 h-10 text-cyan-400/80 mb-2" />
              <span className="text-xs font-medium text-slate-200">
                {file ? file.name : 'Click to select or drag & drop NetCDF file (.nc)'}
              </span>
              <span className="text-[10px] text-slate-500 font-mono mt-1">
                Supported: CF-1.8 Compliant NetCDF4 / HDF5
              </span>
            </label>
          </div>

          {/* Upload Status / Results */}
          {uploading && (
            <div className="p-3 rounded-lg bg-cyan-950/40 border border-cyan-800 text-xs text-cyan-300 font-mono flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
              <span>Validating synoptic tensors & executing forward pass...</span>
            </div>
          )}

          {error && (
            <div className="p-3 rounded-lg bg-red-950/60 border border-red-700 text-xs text-red-300 font-mono flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {response && (
            <div className="p-3.5 rounded-lg bg-emerald-950/40 border border-emerald-700 text-xs space-y-1.5 font-mono">
              <div className="flex items-center space-x-1.5 text-emerald-400 font-bold">
                <CheckCircle2 className="w-4 h-4" />
                <span>Inference Forward Pass Successful</span>
              </div>
              <p className="text-slate-300 text-[11px]">{response.message}</p>
              <div className="text-[10px] text-slate-400 pt-1">
                Detected Variables: {response.detected_variables?.join(', ')}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 border-t border-meteor-700/70 bg-meteor-950/60 flex items-center justify-end space-x-2">
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg text-xs font-mono text-slate-400 hover:text-slate-200 transition-colors"
          >
            Close
          </button>
          <button
            disabled={!file || uploading}
            onClick={handleUpload}
            className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-mono transition-colors shadow"
          >
            Run Inference
          </button>
        </div>
      </div>
    </div>
  );
}
