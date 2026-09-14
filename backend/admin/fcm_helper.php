<?php
/**
 * Firebase Cloud Messaging (FCM) Bildirim Gönderici
 * Firebase Console'dan alınan Server Key veya Service Account ile anlık bildirim iletir.
 */

define('FCM_SERVER_KEY', ''); // Opsiyonel: Firebase Server Key buraya girilebilir

function sendFcmPushNotification($pdo, $title, $body, $dataPayload = []) {
    // 1. Veritabanındaki tüm kayıtlı cihaz tokenlerini al
    try {
        $stmt = $pdo->query("SELECT DISTINCT token FROM device_tokens WHERE token IS NOT NULL AND token != ''");
        $tokens = $stmt->fetchAll(PDO::FETCH_COLUMN);

        if (empty($tokens)) {
            return [
                'success' => true,
                'sent_count' => 0,
                'message' => 'Bildirim veritabanına kaydedildi. (Henüz uygulamayı açmış kayıtlı bir cihaz tokeni yok)'
            ];
        }

        // Eğer Firebase Server Key tanımlıysa FCM sunucusuna istek gönder
        if (!empty(FCM_SERVER_KEY)) {
            $url = 'https://fcm.googleapis.com/fcm/send';

            $fields = [
                'registration_ids' => $tokens,
                'notification'     => [
                    'title'        => $title,
                    'body'         => $body,
                    'sound'        => 'default',
                    'icon'         => 'ic_launcher'
                ],
                'data'             => array_merge($dataPayload, [
                    'title' => $title,
                    'body'  => $body,
                ])
            ];

            $headers = [
                'Authorization: key=' . FCM_SERVER_KEY,
                'Content-Type: application/json'
            ];

            $ch = curl_init();
            curl_setopt($ch, CURLOPT_URL, $url);
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($fields));

            $result = curl_exec($ch);
            curl_close($ch);

            return [
                'success' => true,
                'sent_count' => count($tokens),
                'fcm_response' => json_decode($result, true)
            ];
        }

        return [
            'success' => true,
            'sent_count' => count($tokens),
            'message' => 'Bildirim oluşturuldu ve ' . count($tokens) . ' cihaz listesine hazırlandı.'
        ];
    } catch (Exception $e) {
        return [
            'success' => false,
            'message' => 'Bildirim gönderme hatası: ' . $e->getMessage()
        ];
    }
}
?>
