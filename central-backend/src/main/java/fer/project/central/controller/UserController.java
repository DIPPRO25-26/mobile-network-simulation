package fer.project.central.controller;

import fer.project.central.model.UserEventRequest;
import fer.project.central.model.UserEventResponse;
import fer.project.central.service.UserService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * REST Controller for user events from BTS
 * 
 * MVP Implementation - basic POST endpoint only
 * 
 * TODO for team:
 * - Add HMAC validation interceptor/filter
 * - Add rate limiting
 * - Add request/response logging
 * - Implement error handling with @ControllerAdvice
 * - Add API versioning
 * - Add Swagger/OpenAPI documentation
 */
@RestController
@RequestMapping("/api/v1/user")
@RequiredArgsConstructor
@Slf4j
public class UserController {

    private final UserService userService;

    /**
     * POST /api/v1/user
     * Receives user event from BTS
     * 
     * TODO:
     * - Add @PreAuthorize for security
     * - Validate HMAC signature (check X-HMAC-Signature header)
     * - Validate timestamp (check X-Timestamp header)
     */
    @PostMapping
    public ResponseEntity<UserEventResponse> processUserEvent(
            @Valid @RequestBody UserEventRequest request,
            @RequestHeader(value = "X-HMAC-Signature", required = false) String hmacSignature,
            @RequestHeader(value = "X-Timestamp", required = false) String timestamp) {
        
        log.info("Received user event from BTS: {} for IMEI: {}", request.getBtsId(), request.getImei());

        // TODO: Validate HMAC signature
        // if (!hmacValidator.validate(request, hmacSignature, timestamp)) {
        //     return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        // }

        UserEventResponse response = userService.processUserEvent(request);
        return ResponseEntity.ok(response);
    }

    /**
     * GET /api/v1/user/health
     * Simple health check endpoint
     */
    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("Central Backend is running");
    }
}
