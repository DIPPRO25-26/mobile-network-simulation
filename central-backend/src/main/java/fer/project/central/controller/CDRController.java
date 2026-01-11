package fer.project.central.controller;

import fer.project.central.model.CDRRecord;
import fer.project.central.service.CDRService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;

@RestController
@RequestMapping("/api/v1/cdr")
@RequiredArgsConstructor
public class CDRController {

    private final CDRService cdrService;

    @GetMapping
    public Page<CDRRecord> getAllCDRRecords(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(defaultValue = "timestampArrival,desc") String[] sort
    ) {
        Pageable pageable = PageRequest.of(page, size, Sort.by(parseSortParams(sort)));
        return cdrService.getAllRecords(pageable);
    }

    @GetMapping("/imei/{imei}")
    public Page<CDRRecord> getByImei(
            @PathVariable String imei,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(defaultValue = "timestampArrival,desc") String[] sort
    ) {
        Pageable pageable = PageRequest.of(page, size, Sort.by(parseSortParams(sort)));
        return cdrService.getByImei(imei, pageable);
    }

    @GetMapping("/bts/{btsId}")
    public Page<CDRRecord> getByBtsId(
            @PathVariable String btsId,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(defaultValue = "timestampArrival,desc") String[] sort
    ) {
        Pageable pageable = PageRequest.of(page, size, Sort.by(parseSortParams(sort)));
        return cdrService.getByBtsId(btsId, pageable);
    }

    @GetMapping("/time-range")
    public Page<CDRRecord> getByTimeRange(
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime start,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime end,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
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
