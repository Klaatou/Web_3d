# Renomme la region : fichiers de site\ (NOM.glb, NOM.config.json, NOM.zones.json), default.json, le salon de presence (cle "room") et la fiche de la carte (regions.json).
# Usage : renommer-region.bat NOUVEAU_NOM      (ou double-clic, le nom est alors demande)
param([string]$Nouveau)
$base = Split-Path -Parent $MyInvocation.MyCommand.Path
$site = Join-Path $base 'site'
$defaut = Join-Path $site 'default.json'
$utf8 = New-Object System.Text.UTF8Encoding($false)
if (-not (Test-Path -LiteralPath $defaut)) { Write-Host "default.json introuvable dans le dossier site."; exit 1 }
$texte = [System.IO.File]::ReadAllText($defaut)
if ($texte -notmatch '"region"\s*:\s*"([^"]+)"') { Write-Host "default.json illisible : il doit contenir {""region"": ""NOM""}."; exit 1 }
$ancien = $Matches[1]
Write-Host "Nom actuel de la region : $ancien"
if (-not $Nouveau) { $Nouveau = Read-Host "Nouveau nom (lettres, chiffres, tiret, souligne)" }
if ($Nouveau -notmatch '^[\p{L}\p{N}_-]+$') { Write-Host "Nom refuse : seulement des lettres, des chiffres, - et _ (ni espace, ni point)."; exit 1 }
if ($Nouveau -eq $ancien) { Write-Host "C'est deja le nom actuel : rien a faire."; exit 0 }
foreach ($ext in '.glb', '.config.json', '.zones.json') {
  if (Test-Path -LiteralPath (Join-Path $site ($Nouveau + $ext))) { Write-Host ("Un fichier " + $Nouveau + $ext + " existe deja dans site : abandon, rien n'a ete modifie."); exit 1 }
}
foreach ($ext in '.glb', '.config.json', '.zones.json') {
  $src = Join-Path $site ($ancien + $ext)
  if (Test-Path -LiteralPath $src) { Rename-Item -LiteralPath $src -NewName ($Nouveau + $ext); Write-Host ("  renomme : " + $ancien + $ext + " -> " + $Nouveau + $ext) }
  elseif ($ext -eq '.glb') { Write-Host ("  ATTENTION : " + $ancien + ".glb est introuvable dans site : mettez votre GLB sous le nom " + $Nouveau + ".glb") }
}
[System.IO.File]::WriteAllText($defaut, ($texte -replace ('"region"\s*:\s*"' + [regex]::Escape($ancien) + '"'), ('"region": "' + $Nouveau + '"')), $utf8)
Write-Host "  default.json mis a jour"
$config = Join-Path $site ($Nouveau + '.config.json')
if (Test-Path -LiteralPath $config) {
  $c = [System.IO.File]::ReadAllText($config)
  $c2 = $c -replace ('"room"\s*:\s*"' + [regex]::Escape($ancien) + '"'), ('"room": "' + $Nouveau + '"')
  if ($c2 -ne $c) { [System.IO.File]::WriteAllText($config, $c2, $utf8); Write-Host "  salon de presence (room) mis a jour" }
}
$regions = Join-Path $site 'regions.json'
if (Test-Path -LiteralPath $regions) {
  $r = [System.IO.File]::ReadAllText($regions)
  $r2 = $r -replace ('("(?:id|room)"\s*:\s*")' + [regex]::Escape($ancien) + '"'), ('${1}' + $Nouveau + '"')
  $r2 = $r2 -replace ('(region=)' + [regex]::Escape($ancien) + '(?![\w-])'), ('${1}' + $Nouveau)
  if ($r2 -ne $r) { [System.IO.File]::WriteAllText($regions, $r2, $utf8); Write-Host "  carte (regions.json) mise a jour" }
}
Write-Host "Termine. Rechargez la page (F5) ; le salon de presence s'appelle maintenant $Nouveau."
