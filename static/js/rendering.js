// rendering.js

export function renderResult(data) {
    const historyDiv = document.getElementById('history');
    if (!historyDiv) return;

    let resultHtml = '';

    // Detectar OPEN_URL
    if (typeof data.result_data === 'string' && data.result_data.startsWith('OPEN_URL:')) {
        const url = data.result_data.replace('OPEN_URL:', '');
        window.open(url, '_blank');
        data.result_type = 'open_url';
        data.url = url;
    }

    // Detectar objetos específicos
    if (typeof data.result_data === 'object' && data.result_data !== null) {
        if (data.result_data.type === 'analysis_result') {
            resultHtml = renderAnalysisResult(data.result_data);
        } else if (data.result_data.type === 'clean_result') {
            resultHtml = renderCleanResult(data.result_data);
        } else {
            resultHtml = `<pre class="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg whitespace-pre-wrap">${JSON.stringify(data.result_data, null, 2)}</pre>`;
        }
    } else {
        switch (data.result_type) {
            case 'list':
                resultHtml = data.result_data.map(item => `
                    <div class="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg mb-2">
                        <a href="${item.link}" target="_blank" class="text-blue-600 font-semibold hover:underline">
                            ${escapeHtml(item.title)}
                        </a>
                        <p class="text-sm mt-1">${escapeHtml(item.snippet)}</p>
                        ${
                            data.tool === 'web_search'
                            ? `<button onclick="window.open('${item.link}','_blank')" class="mt-2 px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600">
                                Abrir web
                              </button>`
                            : ''
                        }
                    </div>
                `).join('');
                break;
            case 'open_url':
                resultHtml = `<div class="p-4 bg-blue-50 dark:bg-blue-800 rounded-lg">
                    <p class="font-semibold">${escapeHtml(data.result_data)}</p></div>`;
                break;
            default:
                resultHtml = `<pre class="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg whitespace-pre-wrap">${escapeHtml(data.result_data)}</pre>`;
        }
    }

    const entry = document.createElement('div');
    entry.className = 'entry p-4 bg-white dark:bg-gray-800 rounded-lg shadow-md';
    entry.innerHTML = `
        <div class="font-bold"><span class="text-blue-600">🧠 Tú:</span> ${escapeHtml(data.input)}</div>
        <div class="mt-2"><span class="text-blue-600">🔧 Herramienta:</span> ${escapeHtml(data.tool)}</div>
        <div class="mt-4"><span class="font-bold">📦 Resultado:</span><div class="mt-2">${resultHtml}</div></div>
    `;
    historyDiv.prepend(entry);
}

export function renderAnalysisResult(data) {
    const analysis = data.analysis;
    const stats = data.statistics;

    let html = `<div class="bg-gradient-to-r from-teal-50 to-cyan-50 dark:from-teal-900 dark:to-cyan-900 rounded-lg p-4 space-y-4">
        <div class="flex items-center justify-between border-b border-teal-200 dark:border-teal-700 pb-3">
            <h3 class="text-lg font-bold text-teal-800 dark:text-teal-200">🔍 Análisis: ${escapeHtml(data.filename)}</h3>
            <span class="px-3 py-1 bg-teal-600 text-white rounded-full text-xs font-semibold">
                ${data.success ? '✅ Completado' : '⚠️ Con errores'}
            </span>
        </div>
        <div class="grid grid-cols-2 gap-3">
            <div class="bg-white dark:bg-gray-800 rounded-lg p-3">
                <div class="text-xs text-gray-500 dark:text-gray-400">Puntos de datos</div>
                <div class="text-2xl font-bold text-gray-800 dark:text-gray-200">${stats.data_points.toLocaleString()}</div>
            </div>
            <div class="bg-white dark:bg-gray-800 rounded-lg p-3">
                <div class="text-xs text-gray-500 dark:text-gray-400">Rango (ppm)</div>
                <div class="text-sm font-semibold text-gray-800 dark:text-gray-200">${stats.frequency_range}</div>
            </div>
        </div>
    `;

    if (data.plot_file) {
        html += `<div class="bg-white dark:bg-gray-800 rounded-lg p-3">
            <img src="/download/plot/${data.plot_file}" alt="Análisis del espectro" class="w-full rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer" onclick="window.open('/download/plot/${data.plot_file}', '_blank')">
        </div>`;
    }

    if (data.recommendations?.length) {
        html += `<div class="bg-blue-50 dark:bg-blue-900 rounded-lg p-4">
            <ul class="space-y-1 text-sm text-blue-700 dark:text-blue-300">`;
        data.recommendations.forEach(rec => html += `<li>• ${escapeHtml(rec)}</li>`);
        html += `</ul></div>`;
    }

    html += `</div>`;
    return html;
}

export function renderCleanResult(data) {
    const improvement = data.snr_improvement;
    const improvementColor = improvement > 5 ? 'green' : improvement > 2 ? 'yellow' : 'orange';

    return `<div class="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900 dark:to-emerald-900 rounded-lg p-4 space-y-4">
        <div class="flex items-center justify-between border-b border-green-200 dark:border-green-700 pb-3">
            <h3 class="text-lg font-bold text-green-800 dark:text-green-200">✨ Limpieza Completada</h3>
            <span class="px-3 py-1 bg-green-600 text-white rounded-full text-xs font-semibold">
                ${data.success ? '✅ Exitoso' : '⚠️ Con advertencias'}
            </span>
        </div>
        <div class="grid grid-cols-3 gap-3 text-center">
            <div class="bg-white dark:bg-gray-800 rounded-lg p-3">
                <div class="text-xs text-gray-500 dark:text-gray-400">SNR Original</div>
                <div class="text-xl font-bold text-gray-600 dark:text-gray-400">${data.snr_original.toFixed(1)}</div>
                <div class="text-xs text-gray-500">dB</div>
            </div>
            <div class="bg-white dark:bg-gray-800 rounded-lg p-3">
                <div class="text-xs text-gray-500 dark:text-gray-400">Mejora</div>
                <div class="text-xl font-bold text-${improvementColor}-600">+${improvement.toFixed(1)}</div>
                <div class="text-xs text-gray-500">dB</div>
            </div>
            <div class="bg-white dark:bg-gray-800 rounded-lg p-3">
                <div class="text-xs text-gray-500 dark:text-gray-400">SNR Final</div>
                <div class="text-xl font-bold text-green-600">${data.snr_clean.toFixed(1)}</div>
                <div class="text-xs text-gray-500">dB</div>
            </div>
        </div>
    </div>`;
}
