# Builds transparent sky tiles that repeat above the comic-strip backgrounds on tall (phone) viewports.
# stars.png      night + halloween: flat yellow four-point stars with a thin dark outline, strip style
# stars-dusk.png dusk: a few small pale pink stars
# rain.png       rain: diagonal ink rain lines
Add-Type -AssemblyName System.Drawing
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rand = New-Object System.Random(7)

function New-Tile([int]$size) {
  $bmp = New-Object System.Drawing.Bitmap($size, $size, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $g.Clear([System.Drawing.Color]::Transparent)
  return @($bmp, $g)
}

function Draw-Star($g, [float]$cx, [float]$cy, [float]$r, $fill, $outline, [float]$pen) {
  $pts = New-Object 'System.Collections.Generic.List[System.Drawing.PointF]'
  for ($i = 0; $i -lt 8; $i++) {
    $a = [Math]::PI / 4 * $i - [Math]::PI / 2
    $rr = if ($i % 2 -eq 0) { $r } else { $r * 0.42 }
    $pts.Add((New-Object System.Drawing.PointF(($cx + [Math]::Cos($a) * $rr), ($cy + [Math]::Sin($a) * $rr))))
  }
  $arr = $pts.ToArray()
  $g.FillPolygon((New-Object System.Drawing.SolidBrush($fill)), $arr)
  if ($pen -gt 0) { $g.DrawPolygon((New-Object System.Drawing.Pen($outline, $pen)), $arr) }
}

# stars.png
$t = New-Tile 720; $bmp = $t[0]; $g = $t[1]
$yellow = [System.Drawing.Color]::FromArgb(255, 246, 213, 92)
$ink = [System.Drawing.Color]::FromArgb(255, 38, 38, 42)
$placed = @()
for ($n = 0; $n -lt 11; $n++) {
  $ok = $false; $tries = 0
  while (-not $ok -and $tries -lt 50) {
    $x = $rand.Next(50, 670); $y = $rand.Next(50, 670); $r = $rand.Next(14, 30)
    $ok = $true
    foreach ($p in $placed) { if ([Math]::Sqrt(($p[0]-$x)*($p[0]-$x) + ($p[1]-$y)*($p[1]-$y)) -lt 120) { $ok = $false; break } }
    $tries++
  }
  if ($ok) { $placed += ,@($x, $y); Draw-Star $g $x $y $r $yellow $ink 2.2 }
}
$bmp.Save("$dir\stars.png", [System.Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()

# stars-dusk.png
$t = New-Tile 720; $bmp = $t[0]; $g = $t[1]
$pink = [System.Drawing.Color]::FromArgb(255, 236, 196, 206)
$placed = @()
for ($n = 0; $n -lt 5; $n++) {
  $ok = $false; $tries = 0
  while (-not $ok -and $tries -lt 50) {
    $x = $rand.Next(60, 660); $y = $rand.Next(60, 660); $r = $rand.Next(10, 18)
    $ok = $true
    foreach ($p in $placed) { if ([Math]::Sqrt(($p[0]-$x)*($p[0]-$x) + ($p[1]-$y)*($p[1]-$y)) -lt 160) { $ok = $false; break } }
    $tries++
  }
  if ($ok) { $placed += ,@($x, $y); Draw-Star $g $x $y $r $pink $ink 1.6 }
}
$bmp.Save("$dir\stars-dusk.png", [System.Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()

# rain.png (lines slant down-left like the scene: dx = -0.35 per dy)
$t = New-Tile 600; $bmp = $t[0]; $g = $t[1]
$rainPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(255, 60, 74, 92), 2.4)
$rainPen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round; $rainPen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
for ($n = 0; $n -lt 34; $n++) {
  $x = $rand.Next(0, 600); $y = $rand.Next(0, 600); $len = $rand.Next(50, 130)
  $g.DrawLine($rainPen, [float]$x, [float]$y, [float]($x - 0.35 * $len), [float]($y + $len))
}
$bmp.Save("$dir\rain.png", [System.Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()

Get-ChildItem $dir -Filter *.png | Select-Object Name, Length
