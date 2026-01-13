package fer.project.central.controller;

import fer.project.central.model.CDRRecord;
import fer.project.central.service.CDRService;
import io.swagger.v3.oas.annotations.Operation;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;

@RestController
@RequestMapping("/api/v1/cdr")
@RequiredArgsConstructor
@Validated
public class CDRController {

    private static final int MAX_PAGE_SIZE = 100;

    private final CDRService cdrService;

    @Operation(
            summary = "Get all CDR records",
            description = "Retrieves a paginated list of all Call Detail Records with optional sorting"
    )
    @GetMapping
    public Page<CDRRecord> getAllCDRRecords(
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(MAX_PAGE_SIZE) int size,
            @RequestParam(defaultValue = "timestampArrival,desc") String[] sort
    ) {
        Pageable pageable = PageRequest.of(page, size, Sort.by(parseSortParams(sort)));
        return cdrService.getAllRecords(pageable);
    }

    @Operation(
            summary = "Get CDR records by IMEI",
            description = "Retrieves paginated CDR records filtered by International Mobile Equipment Identity"
    )
    @GetMapping("/imei/{imei}")
    public Page<CDRRecord> getByImei(
            @PathVariable String imei,
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(MAX_PAGE_SIZE) int size,
            @RequestParam(defaultValue = "timestampArrival,desc") String[] sort
    ) {
        Pageable pageable = PageRequest.of(page, size, Sort.by(parseSortParams(sort)));
        return cdrService.getByImei(imei, pageable);
    }

    @Operation(
            summary = "Get CDR records by BTS ID",
            description = "Retrieves paginated CDR records filtered by Base Transceiver Station identifier"
    )
    @GetMapping("/bts/{btsId}")
    public Page<CDRRecord> getByBtsId(
            @PathVariable String btsId,
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(MAX_PAGE_SIZE) int size,
            @RequestParam(defaultValue = "timestampArrival,desc") String[] sort
    ) {
        Pageable pageable = PageRequest.of(page, size, Sort.by(parseSortParams(sort)));
        return cdrService.getByBtsId(btsId, pageable);
    }

    @Operation(
            summary = "Get CDR records by time range",
            description = "Retrieves paginated CDR records within a specified time range"
    )
    @GetMapping("/time-range")
    public Page<CDRRecord> getByTimeRange(
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime start,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime end,
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(MAX_PAGE_SIZE) int size,
            @RequestParam(defaultValue = "timestampArrival,desc") String[] sort
            ) {
        Pageable pageable = PageRequest.of(page, size, Sort.by(parseSortParams(sort)));
        return cdrService.getByTimeRange(start, end, pageable);
    }

    private Sort.Order[] parseSortParams(String[] sort) {
        return new Sort.Order[] {
                Sort.Order.by(sort[0]).with(
                        sort.length > 1 && sort[1].equalsIgnoreCase("desc")
                                ? Sort.Direction.DESC
                                : Sort.Direction.ASC
                )
        };
    }
}
