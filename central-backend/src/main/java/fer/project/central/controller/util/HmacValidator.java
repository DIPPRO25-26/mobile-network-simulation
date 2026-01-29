package fer.project.central.controller.util;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

@Component
@Slf4j
public class HmacValidator {

    private final String secretKey;

    public HmacValidator(@Value("${hmac.secret-key}") String secretKey) {
        this.secretKey = secretKey;
        log.warn("HMACV INIT secretKeyLength={}", secretKey == null ? -1 : secretKey.length());
    }

    public boolean validate(String body, String timestamp, String receivedSignature) {
        try {
            String bodySafe = body == null ? "" : body;
            String tsSafe = timestamp == null ? "" : timestamp;
            String recSafe = receivedSignature == null ? "" : receivedSignature;

            // payload koji se potpisuje (kod tebe: body + timestamp)
            String message = bodySafe + tsSafe;

            String calculatedSignature = calculateHmac(message);

            // ---- DEBUG LOGS ----
            log.warn("HMACV DEBUG body='{}'", bodySafe);
            log.warn("HMACV DEBUG ts='{}' (len={})", tsSafe, tsSafe.length());
            log.warn("HMACV DEBUG payload='{}'", message);

            log.warn("HMACV DEBUG expected(hex)='{}' (len={})", calculatedSignature, calculatedSignature.length());
            log.warn("HMACV DEBUG received='{}' (len={})", recSafe, recSafe.length());

            boolean eqRaw = calculatedSignature.equals(recSafe);
            boolean eqTrim = calculatedSignature.equals(recSafe.trim());
            boolean eqIgnoreCase = calculatedSignature.equalsIgnoreCase(recSafe);
            boolean eqIgnoreCaseTrim = calculatedSignature.equalsIgnoreCase(recSafe.trim());

            log.warn("HMACV DEBUG equalsRaw={} equalsTrim={} equalsIgnoreCase={} equalsIgnoreCaseTrim={}",
                    eqRaw, eqTrim, eqIgnoreCase, eqIgnoreCaseTrim);

            // stvarna validacija (zadrži strogo pravilo kako si imala)
            return calculatedSignature.equalsIgnoreCase(receivedSignature.trim());

        } catch (Exception e) {
            log.error("Error while validating HMAC", e);
            return false;
        }
    }

    private String calculateHmac(String message) throws NoSuchAlgorithmException, InvalidKeyException {
        Mac mac = Mac.getInstance("HmacSHA256");

        // BITNO: tvoj key se tretira kao UTF-8 string (NE base64 decode).
        SecretKeySpec secretKeySpec =
                new SecretKeySpec(secretKey.getBytes(StandardCharsets.UTF_8), "HmacSHA256");

        mac.init(secretKeySpec);

        byte[] hmacBytes = mac.doFinal(message.getBytes(StandardCharsets.UTF_8));

        // hex (lowercase) potpis
        return HexFormat.of().formatHex(hmacBytes);
    }
}