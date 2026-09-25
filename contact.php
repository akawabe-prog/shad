<?php
declare(strict_types=1);

/*
 * SHAD JAPAN お問い合わせ受付
 * 参照: eXs (exs.customjapan.net) の contact.php と同じ方式
 *   - POST を検証し、info@customjapan.jp へメール送信
 *   - 成功: thanks.html / 失敗・不備: form-error.html へリダイレクト
 */

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Location: contact.html');
    exit;
}

mb_internal_encoding('UTF-8');

function posted(string $key): string
{
    return trim((string)($_POST[$key] ?? ''));
}

// --- スパム対策（ハニーポット）: 人間には非表示の website に入力があれば無視 ---
if (posted('website') !== '') {
    header('Location: thanks');
    exit;
}

$topicCodes = [
    'product'  => '製品について（仕様・使い方）',
    'fit'      => '適合・取り付けについて',
    'order'    => '購入・お届け・返品について',
    'warranty' => '保証・不具合・補修部品について',
    'dealer'   => '取扱店・SHAD BASE になりたい',
    'press'    => '取材・OEM・その他',
];

$topic   = posted('topic');
$name    = posted('name');
$company = posted('company');
$email   = posted('email');
$tel     = posted('tel');
$bike    = posted('bike');
$product = posted('product');
$message = posted('message');
$agree   = (string)($_POST['agree'] ?? '');

$errors = [];
if (!isset($topicCodes[$topic])) {
    $errors[] = 'topic';
}
if ($name === '') {
    $errors[] = 'name';
}
if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    $errors[] = 'email';
}
if (mb_strlen($message) < 10) {
    $errors[] = 'message';
}
if ($agree !== 'on' && $agree !== '1') {
    $errors[] = 'agree';
}
// 適合・取り付けの相談は車種必須
if ($topic === 'fit' && $bike === '') {
    $errors[] = 'bike';
}

if (!empty($errors)) {
    header('Location: form-error.html?form=contact');
    exit;
}

$topicLabel = $topicCodes[$topic];

$to = 'info@customjapan.jp';
$subject = '【SHAD JAPAN】お問い合わせ（' . $topicLabel . '）';
$body = implode("\n", [
    'SHAD JAPAN サイトのお問い合わせフォームより送信されました。',
    '',
    'お問い合わせ種別: ' . $topicLabel,
    'お名前: ' . $name,
    '会社名・店舗名: ' . ($company !== '' ? $company : '-'),
    'メールアドレス: ' . $email,
    '電話番号: ' . ($tel !== '' ? $tel : '-'),
    '車種: ' . ($bike !== '' ? $bike : '-'),
    '製品名・品番: ' . ($product !== '' ? $product : '-'),
    '',
    '── お問い合わせ内容 ──',
    $message,
    '',
    '---',
    '送信日時: ' . date('Y-m-d H:i:s'),
    '送信元IP: ' . ($_SERVER['REMOTE_ADDR'] ?? '-'),
    'UA: ' . ($_SERVER['HTTP_USER_AGENT'] ?? '-'),
]);

$headers = [
    'From: noreply@shad-japan.com',   // ※送信ドメインのSPF/DKIM設定が必要
    'Reply-To: ' . $email,
    'Content-Type: text/plain; charset=UTF-8',
];

$sent = false;
if (function_exists('mb_send_mail')) {
    $sent = mb_send_mail($to, $subject, $body, implode("\r\n", $headers));
} else {
    $sent = mail($to, $subject, $body, implode("\r\n", $headers));
}

header('Location: ' . ($sent ? 'thanks' : 'form-error'));
exit;
