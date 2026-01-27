package fer.project.central.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import fer.project.central.model.UserEventRequest;
import fer.project.central.model.UserEventResponse;
import fer.project.central.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validator;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Set;

@RestController
@RequestMapping("/api/v1/user")
@RequiredArgsConstructor
@Slf4j
public class UserController {

    private final UserService userService;
    private final ObjectMapper objectMapper;
    private final Validator validator;

    @Operation(
            summary = "Process user event from BTS",
            description = "Receives information about user presence from Base Transceiver Station."
    )
    @PostMapping
    public ResponseEntity<UserEventResponse> processUserEvent(@RequestBody String rawBody) {

        UserEventRequest request;
        try {
            request = objectMapper.readValue(rawBody, UserEventRequest.class);
        } catch (Exception e) {
            log.error("Failed to parse request body", e);
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).build();
        }

        Set<ConstraintViolation<UserEventRequest>> violations = validator.validate(request);
        if (!violations.isEmpty()) {
            log.warn("Validation failed: {}", violations);
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).build();
        }

        log.info("Received user event from BTS: {} for IMEI: {}", request.getBtsId(), request.getImei());

        UserEventResponse response = userService.processUserEvent(request);
        return ResponseEntity.ok(response);
    }
}