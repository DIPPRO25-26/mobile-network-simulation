package fer.project.central.controller;

import fer.project.central.model.BTS;
import fer.project.central.service.BTSService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/bts")
@RequiredArgsConstructor
public class BTSController {

    private final BTSService btsService;

    @Operation(
            summary = "Get all BTS",
            description = "Retrieves a list of all Base Transceiver Stations from the registry"
    )
    @ApiResponse(
            responseCode = "200",
            description = "Successfully retrieved list of BTS",
            content = @Content(schema = @Schema(implementation = BTS.class))
    )
    @GetMapping
    public ResponseEntity<List<BTS>> getAllBTS() {
        return ResponseEntity.ok(btsService.getAllBTS());
    }

    @Operation(
            summary = "Get BTS by ID",
            description = "Retrieves a specific Base Transceiver Station by its BTS ID"
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "Successfully retrieved BTS",
                    content = @Content(schema = @Schema(implementation = BTS.class))
            ),
            @ApiResponse(
                    responseCode = "404",
                    description = "BTS not found",
                    content = @Content
            )
    })
    @GetMapping("/{btsId}")
    public ResponseEntity<BTS> getBTSByBtsId(
            @Parameter(description = "BTS identifier", required = true)
            @PathVariable String btsId
    ) {
        return btsService.getBTSByBtsId(btsId)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @Operation(
            summary = "Update BTS status",
            description = "Updates the status of a Base Transceiver Station. Only updates if the status has changed."
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "Successfully updated BTS status",
                    content = @Content(schema = @Schema(implementation = BTS.class))
            ),
            @ApiResponse(
                    responseCode = "400",
                    description = "Invalid request - status field missing",
                    content = @Content
            ),
            @ApiResponse(
                    responseCode = "404",
                    description = "BTS not found",
                    content = @Content
            )
    })
    @PatchMapping("/{btsId}/status")
    public ResponseEntity<BTS> updateBTSStatus(
            @Parameter(description = "BTS identifier", required = true)
            @PathVariable String btsId,
            @io.swagger.v3.oas.annotations.parameters.RequestBody(
                    description = "Status update payload",
                    required = true,
                    content = @Content(
                            schema = @Schema(example = "{\"status\": \"active\"}")
                    )
            )
            @RequestBody Map<String, String> statusUpdate
            ) {
        try {
            String status = statusUpdate.get("status");
            if (status == null) {
                return ResponseEntity.badRequest().build();
            }
            BTS updatedBts = btsService.updateBTSStatus(btsId, status);
            return ResponseEntity.ok(updatedBts);
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
}
