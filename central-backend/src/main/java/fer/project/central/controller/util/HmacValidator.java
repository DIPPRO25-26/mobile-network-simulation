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
    }

    public boolean validate(String body, String timestamp, String receivedSignature) {
        try {
            String message = body + timestamp;
            String calculatedSignature = calculateHmac(message);

            return calculatedSignature.equals(receivedSignature);
        } catch (Exception e) {
            log.error("Error while validating HMAC", e);
            return false;
        }
    }

    private String calculateHmac(String message) throws NoSuchAlgorithmException, InvalidKeyException {
        Mac mac = Mac.getInstance("HmacSHA256");
        SecretKeySpec secretKeySpec = new SecretKeySpec(secretKey.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
        mac.init(secretKeySpec);
        byte[] hmacBytes = mac.doFinal(message.getBytes(StandardCharsets.UTF_8));
        String hexSignature = HexFormat.of().formatHex(hmacBytes);

        return hexSignature;
    }
}
