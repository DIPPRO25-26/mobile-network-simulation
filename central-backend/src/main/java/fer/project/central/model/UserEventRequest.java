package fer.project.central.model;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * DTO for receiving user event data from BTS
 * 
 * MVP Implementation - basic fields only
 * 
 * TODO for team:
 * - Add custom validation annotations
 * - Validate IMEI format (15 digits)
 * - Validate MCC/MNC codes
 * - Add builder pattern for easier testing
 */
@Data
public class UserEventRequest {

    @NotBlank(message = "IMEI is required")
    private String imei;

    @NotBlank(message = "MCC is required")
    private String mcc;

    @NotBlank(message = "MNC is required")
    private String mnc;

    @NotBlank(message = "LAC is required")
    private String lac;

    @NotBlank(message = "BTS ID is required")
    private String btsId;

    @NotNull(message = "Timestamp is required")
    private LocalDateTime timestamp;

    private UserLocation userLocation;

    @Data
    public static class UserLocation {
        private Double x;
        private Double y;
    }
}
