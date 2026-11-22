# MaxKB 模型批量配置脚本（v2：修正 model_form 需要 model_name，并支持已存在则跳过）
$ErrorActionPreference = 'Stop'
$Base = 'http://127.0.0.1:8080/admin/api'
$Workspace = 'default'
$DashScopeKey = $env:MAXKB_DASHSCOPE_KEY
$UrlCompat = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
$UrlNative = 'https://dashscope.aliyuncs.com/api/v1'
$RelayKey = $env:MAXKB_RELAY_KEY
$RelayBase = 'https://api.commandcode.ai/provider/v1'

function Post-Json($Url, $Headers, $Obj) {
    $json = $Obj | ConvertTo-Json -Depth 12 -Compress
    $bytes = [Text.Encoding]::UTF8.GetBytes($json)
    return Invoke-RestMethod -Uri $Url -Method Post -Headers $Headers -Body $bytes -ContentType 'application/json' -TimeoutSec 120
}

$login = Post-Json "$Base/user/login" @{} @{ username = 'admin'; password = $env:MAXKB_PASSWORD }
if ($login.code -ne 200) { throw "登录失败: $($login.message)" }
$H = @{ Authorization = "Bearer $($login.data.token)" }
Write-Output '登录成功'

# 已存在的模型名
$existing = (Invoke-RestMethod -Uri "$Base/workspace/$Workspace/model_list" -Headers $H -TimeoutSec 30).data
$existingNames = @()
if ($existing) { $existingNames = @($existing | ForEach-Object { $_.name }) }
Write-Output ("已存在模型: {0}" -f ($existingNames -join ', '))
Write-Output ''

$Models = @(
    @{ provider = 'aliyun_bai_lian_model_provider'; name = '百炼-Embedding';   type = 'EMBEDDING'; model = 'qwen3.7-text-embedding'; url = $UrlCompat; params = @{ dimensions = 1024 } }
    @{ provider = 'aliyun_bai_lian_model_provider'; name = '百炼-Rerank';      type = 'RERANKER';  model = 'qwen3.7-text-rerank';   url = $UrlNative; params = @{ top_n = 3 } }
    @{ provider = 'aliyun_bai_lian_model_provider'; name = '百炼-视觉理解';     type = 'IMAGE';     model = 'qwen3-vl-plus';         url = $UrlNative; params = @{} }
    @{ provider = 'aliyun_bai_lian_model_provider'; name = '百炼-生图';        type = 'TTI';       model = 'qwen-image-3.0';        url = $UrlNative; params = @{ size = '1024*1024'; style = '<auto>'; n = 1 } }
    @{ provider = 'aliyun_bai_lian_model_provider'; name = '百炼-语音合成';     type = 'TTS';       model = 'qwen3-tts-flash';       url = $UrlNative; params = @{ voice = 'Cherry'; speech_rate = 1 } }
    @{ provider = 'aliyun_bai_lian_model_provider'; name = '百炼-语音识别';     type = 'STT';       model = 'qwen3-asr-flash';       url = $UrlNative; params = @{}; cred = @{ type = 'qwen' } }
    @{ provider = 'aliyun_bai_lian_model_provider'; name = '百炼-文生视频';     type = 'TTV';       model = 'wan2.7-t2v';            url = $UrlNative; params = @{} }
    @{ provider = 'aliyun_bai_lian_model_provider'; name = '百炼-图生视频';     type = 'ITV';       model = 'wan2.7-i2v';            url = $UrlNative; params = @{} }
    @{ provider = 'openai_model_provider';           name = 'DeepSeek-Flash';  type = 'LLM';       model = 'deepseek/deepseek-v4.1-flash'; url = $RelayBase; params = @{}; key = $RelayKey }
)

foreach ($m in $Models) {
    Write-Output ('-' * 62)
    Write-Output ("{0}  [{1} / {2}]" -f $m.name, $m.type, $m.model)
    if ($existingNames -contains $m.name) { Write-Output '  ↷ 已存在，跳过'; continue }
    try {
        $apiKey = if ($m.key) { $m.key } else { $DashScopeKey }
        $formUrl = "$Base/provider/model_form?provider=$($m.provider)&model_type=$($m.type)&model_name=$([uri]::EscapeDataString($m.model))"
        $form = (Invoke-RestMethod -Uri $formUrl -Headers $H -TimeoutSec 30).data

        $cred = @{}
        if ($form) {
            foreach ($f in $form) {
                $fld = $f.field
                $val = $f.default_value
                if ($fld -in @('api_base', 'api_url')) { $val = $m.url }
                elseif ($fld -in @('api_key', 'dashscope_api_key')) { $val = $apiKey }
                if ($m.cred -and $m.cred.ContainsKey($fld)) { $val = $m.cred[$fld] }
                if ($null -ne $val -and "$val" -ne '') { $cred[$fld] = $val }
            }
        } else {
            $cred = @{ api_base = $m.url; api_key = $apiKey }
        }

        $pUrl = "$Base/provider/model_params_form?provider=$($m.provider)&model_type=$($m.type)&model_name=$([uri]::EscapeDataString($m.model))"
        $pf = (Invoke-RestMethod -Uri $pUrl -Headers $H -TimeoutSec 30).data
        $pd = @()
        if ($pf) { $pd = @($pf) }
        foreach ($item in $pd) {
            if ($m.params.ContainsKey($item.field)) { $item.default_value = $m.params[$item.field] }
        }

        $res = Post-Json "$Base/workspace/$Workspace/model" $H @{
            name = $m.name; provider = $m.provider; model_type = $m.type; model_name = $m.model
            credential = $cred; model_params_form = $pd
        }
        if ($res.code -eq 200) { Write-Output ("  ✓ 成功  id={0}" -f $res.data.id) }
        else { Write-Output ("  ✗ 失败: {0}" -f $res.message) }
    } catch {
        $msg = $_.Exception.Message
        if ($_.ErrorDetails.Message) { try { $msg = ($_.ErrorDetails.Message | ConvertFrom-Json).message } catch { $msg = $_.ErrorDetails.Message } }
        Write-Output ("  ✗ 异常: {0}" -f $msg)
    }
}

Write-Output ('=' * 62)
Write-Output '=== 当前模型列表 ==='
$list = (Invoke-RestMethod -Uri "$Base/workspace/$Workspace/model_list" -Headers $H -TimeoutSec 30).data
$list | Select-Object name, model_type, model_name, @{n = '状态'; e = { $_.status } } | Format-Table -AutoSize
