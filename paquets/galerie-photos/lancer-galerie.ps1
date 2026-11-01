# Sert le dossier site sur http://localhost (cette machine seulement) et ouvre la galerie
$base = Split-Path -Parent $MyInvocation.MyCommand.Path
$racine = (Resolve-Path (Join-Path $base 'site')).Path.TrimEnd('\')
$types = @{ '.html'='text/html; charset=utf-8'; '.js'='text/javascript; charset=utf-8'; '.mjs'='text/javascript; charset=utf-8'
  '.json'='application/json; charset=utf-8'; '.txt'='text/plain; charset=utf-8'; '.glb'='model/gltf-binary'
  '.jpg'='image/jpeg'; '.jpeg'='image/jpeg'; '.png'='image/png'; '.webp'='image/webp'; '.gif'='image/gif'; '.ico'='image/x-icon' }
$ecoute = New-Object System.Net.HttpListener
$port = 0
foreach ($p in 8000..8020) {
  $ecoute.Prefixes.Clear(); $ecoute.Prefixes.Add("http://localhost:$p/")
  try { $ecoute.Start(); $port = $p; break } catch { }
}
if ($port -eq 0) { Write-Host "Impossible de demarrer le serveur local."; Read-Host "Entree pour fermer"; exit 1 }
Write-Host "Galerie sur http://localhost:$port/ - fermez cette fenetre pour arreter."
Start-Process "http://localhost:$port/"
while ($ecoute.IsListening) {
  $ctx = $ecoute.GetContext()
  try {
    $rel = [Uri]::UnescapeDataString($ctx.Request.Url.AbsolutePath.TrimStart('/'))
    if ($rel -eq '') { $rel = 'index.html' }
    $chemin = [System.IO.Path]::GetFullPath((Join-Path $racine $rel))
    if (-not $chemin.StartsWith($racine + '\') -or -not (Test-Path -LiteralPath $chemin -PathType Leaf)) { $ctx.Response.StatusCode = 404 }
    else {
      $ext = [System.IO.Path]::GetExtension($chemin).ToLower()
      $ctx.Response.ContentType = $(if ($types.ContainsKey($ext)) { $types[$ext] } else { 'application/octet-stream' })
      $o = [System.IO.File]::ReadAllBytes($chemin)
      $ctx.Response.ContentLength64 = $o.Length
      $ctx.Response.OutputStream.Write($o, 0, $o.Length)
    }
  } catch { }
  try { $ctx.Response.Close() } catch { }
}
