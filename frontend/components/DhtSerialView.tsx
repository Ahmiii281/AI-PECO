import React, { useEffect, useRef, useState } from 'react';

type Sample = { ts: number; temperature: number; humidity: number };

const MAX_SAMPLES = 60;
const SERIAL_BAUD = 115200;

export default function DhtSerialView(): JSX.Element {
  const [available, setAvailable] = useState<boolean>(false);
  const [port, setPort] = useState<any | null>(null);
  const [connected, setConnected] = useState(false);
  const [status, setStatus] = useState('idle');
  const [last, setLast] = useState<Sample | null>(null);
  const [samples, setSamples] = useState<Sample[]>([]);
  const readerRef = useRef<any>(null);
  const keepReadingRef = useRef(false);

  useEffect(() => {
    setAvailable(typeof navigator !== 'undefined' && 'serial' in navigator);
    return () => {
      disconnect().catch(() => {});
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function requestPort() {
    try {
      // no filters so user can pick CP210x/FTDI etc.
      const p = await (navigator as any).serial.requestPort();
      setPort(p);
      return p;
    } catch (err) {
      setStatus('port_request_cancelled');
      throw err;
    }
  }

  async function connect() {
    setStatus('connecting');
    try {
      const p = port || (await requestPort());
      await p.open({ baudRate: SERIAL_BAUD });
      setPort(p);
      setConnected(true);
      setStatus('connected');
      keepReadingRef.current = true;
      readLoop(p);
    } catch (err: any) {
      console.error(err);
      setStatus('connect_failed');
      setConnected(false);
    }
  }

  async function disconnect() {
    keepReadingRef.current = false;
    setConnected(false);
    setStatus('closing');
    try {
      if (readerRef.current) {
        await readerRef.current.cancel();
        readerRef.current = null;
      }
      if (port) {
        await port.close();
        setPort(null);
      }
      setStatus('closed');
    } catch (err) {
      console.warn('disconnect error', err);
      setStatus('close_error');
    }
  }

  async function readLoop(p: any) {
    // line-splitting TextDecoderStream -> TransformStream pattern
    try {
      const textStream = p.readable.pipeThrough(new TextDecoderStream());
      let buffer = '';
      const lineSplitter = new TransformStream({
        transform(chunk: string, controller) {
          buffer += chunk;
          const parts = buffer.split(/\r?\n/);
          buffer = parts.pop() || '';
          for (const ln of parts) controller.enqueue(ln);
        },
        flush(controller) {
          if (buffer) controller.enqueue(buffer);
          buffer = '';
        },
      });

      const reader = textStream.pipeThrough(lineSplitter).getReader();
      readerRef.current = reader;

      while (keepReadingRef.current) {
        const { value, done } = await reader.read();
        if (done) break;
        if (!value) continue;
        handleLine(value.trim());
      }

      try {
        await reader.cancel();
      } catch (e) {
        /* ignore */
      }
    } catch (err) {
      console.error('readLoop', err);
      setStatus('read_error');
      setConnected(false);
    }
  }

  function handleLine(line: string) {
    // firmware emits JSON single-line records; ignore other text gracefully
    let j: any = null;
    try {
      if (line.startsWith('{')) j = JSON.parse(line);
    } catch (e) {
      // not JSON — ignore
      return;
    }

    if (!j) return;

    // support both our JSON schema and legacy lines
    if (j.temperature_c != null && j.humidity != null) {
      const sample: Sample = { ts: j.ts_ms || Date.now(), temperature: Number(j.temperature_c), humidity: Number(j.humidity) };
      pushSample(sample);
      setStatus('ok');
      return;
    }

    // fallback: detect human-friendly lines like "Humidity: 56.3 %  Temperature: 24.1 °C"
    if (typeof line === 'string' && /Humidity:\s*\d+/i.test(line)) {
      const tMatch = line.match(/Temperature:\s*([0-9.+-]+)/i);
      const hMatch = line.match(/Humidity:\s*([0-9.+-]+)/i);
      if (tMatch && hMatch) {
        const sample: Sample = { ts: Date.now(), temperature: Number(tMatch[1]), humidity: Number(hMatch[1]) };
        pushSample(sample);
        setStatus('ok');
      }
    }

    // handle diagnostics / errors from device
    if (j.error) {
      setStatus(String(j.error));
    }
  }

  function pushSample(s: Sample) {
    setLast(s);
    setSamples((prev) => {
      const next = [...prev, s].slice(-MAX_SAMPLES);
      return next;
    });
  }

  // tiny sparkline generator (svg polyline points)
  function sparkline(values: number[], w = 160, h = 36) {
    if (!values || values.length === 0) return null;
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;
    return values
      .map((v, i) => {
        const x = (i / Math.max(1, values.length - 1)) * w;
        const y = h - ((v - min) / range) * h;
        return `${x},${y}`;
      })
      .join(' ');
  }

  return (
    <div className="p-6">
      <div className="max-w-3xl mx-auto bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-100">Live DHT22 (Web Serial)</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Connect your ESP32 (USB) and stream temperature & humidity in real time.</p>
          </div>
          <div className="text-right">
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${connected ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
              {connected ? 'Connected' : 'Disconnected'}
            </div>
            <div className="mt-2 text-xs text-gray-500">Status: <span className="font-medium text-gray-700">{status}</span></div>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center space-x-6">
              <div>
                <div className="text-xs text-gray-500">Temperature</div>
                <div className="mt-1 text-4xl font-bold text-gray-800 dark:text-gray-100">{last ? `${last.temperature.toFixed(1)}°C` : '—'}</div>
                <div className="text-sm text-gray-500">{last ? `${(last.temperature * 9 / 5 + 32).toFixed(1)}°F` : ''}</div>
              </div>

              <div>
                <div className="text-xs text-gray-500">Humidity</div>
                <div className="mt-1 text-4xl font-bold text-gray-800 dark:text-gray-100">{last ? `${last.humidity.toFixed(1)}%` : '—'}</div>
                <div className="text-sm text-gray-500">{last ? new Date(last.ts).toLocaleTimeString() : ''}</div>
              </div>

              <div className="ml-4 hidden md:block">
                <svg width="160" height="36" className="bg-gray-50 rounded-md">
                  <polyline
                    fill="none"
                    stroke="#10B981"
                    strokeWidth={2}
                    points={sparkline(samples.map((s) => s.temperature), 160, 36) || ''}
                  />
                </svg>
                <div className="text-xs text-gray-400 mt-1">last {samples.length} samples</div>
              </div>
            </div>
          </div>

          <div className="col-span-1 flex flex-col items-stretch">
            <div className="flex space-x-2">
              <button
                onClick={() => (connected ? disconnect() : connect())}
                className={`flex-1 inline-flex items-center justify-center px-4 py-2 rounded-md text-white font-medium ${connected ? 'bg-red-500 hover:bg-red-600' : 'bg-green-600 hover:bg-green-700'}`}
              >
                {connected ? 'Disconnect' : 'Connect (Web Serial)'}
              </button>
              <button
                onClick={async () => {
                  // quick permission / port chooser
                  try {
                    await requestPort();
                    setStatus('port_selected');
                  } catch (e) {
                    setStatus('port_select_cancel');
                  }
                }}
                className="inline-flex items-center justify-center px-4 py-2 rounded-md border border-gray-200 dark:border-gray-700 text-sm text-gray-600 dark:text-gray-300 bg-white dark:bg-gray-700"
              >
                Choose port
              </button>
            </div>

            <div className="mt-3 text-xs text-gray-500">
              <p>Browser: Chrome / Edge (supports Web Serial). App must be served from <code>http://localhost</code> or over HTTPS.</p>
              <p className="mt-2">Serial baud: <strong>{SERIAL_BAUD}</strong>. Select the COM port used by your ESP32 (e.g. COM6).</p>
            </div>

            <div className="mt-4 text-sm text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 p-3 rounded">
              <div className="font-medium">Recent raw line</div>
              <pre className="mt-2 text-xs text-gray-700 dark:text-gray-100 max-h-24 overflow-auto">{last ? JSON.stringify({ temperature_c: last.temperature, humidity: last.humidity, ts: last.ts }, null, 0) : '—'}</pre>
            </div>
          </div>
        </div>
      </div>

      {!available && (
        <div className="mt-6 max-w-3xl mx-auto text-sm text-yellow-600">Your browser doesn't appear to support the Web Serial API. Use Chrome / Edge on desktop or serve the ESP32 readings over Wi‑Fi (I can help).</div>
      )}
    </div>
  );
}
