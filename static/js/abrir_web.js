// Abrir URLs en nueva ventana
export function abrirWeb(url) {
    if (!url.match(/^https?:\/\//)) url = 'https://' + url;
    window.open(url, '_blank');
}
