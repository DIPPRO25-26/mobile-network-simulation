package fer.project.central.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * DTO for responding to BTS with previous location data
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserEventResponse {

    private String status;
    private ResponseData data;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ResponseData {
        private PreviousLocation previousLocation;
        private Long cdrId;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class PreviousLocation {
        private String btsId;
        private String lac;
        private LocalDateTime lastSeen;
    }

    public static UserEventResponse success(PreviousLocation previousLocation, Long cdrId) {
        UserEventResponse response = new UserEventResponse();
        response.setStatus("success");
        response.setData(new ResponseData(previousLocation, cdrId));
        return response;
    }
}
